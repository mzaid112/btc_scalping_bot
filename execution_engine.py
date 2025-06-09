from config_manager import unlock_passwords
secrets = unlock_passwords()
import MetaTrader5 as mt5
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from utils.indicators import get_recent_indicators
from strategy_engine import get_trade_signal
from risk_manager import is_risk_exceeded
from comms_whatsapp import send_whatsapp_message
from trade_logger import log_trade
from pnl_tracker import record_trade_summary
from learning_agents import is_pattern_profitable
from utils.indicators import add_indicators
from learning_agents import save_pattern_memory, log_pattern_memory
from pnl_tracker import log_trade
from learning_agents import extract_pattern_features
import uuid
from config_manager import unlock_passwords
secrets = unlock_passwords()


current_trade_active = False  # ✅ New global trade status tracker


# === Configuration ===
def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

# === Connect to MT5 ===
def connect_mt5():
    config = load_config()
    if not mt5.initialize():
        raise RuntimeError("MT5 init failed:", mt5.last_error())

    # Replace the login section with this:
    account_id = os.getenv("MT5_ACCOUNT_ID")
    password = secrets["MT5_PASSWORD"]
    server = os.getenv("MT5_SERVER")
    
    authorized = mt5.login(
        int(account_id),
        password=password,
        server=server
    )

    if not authorized:
        raise RuntimeError("MT5 login failed:", mt5.last_error())
    else:
        print("✅ Connected to MT5")

# === Calculate dynamic SL/TP using ATR ===
def calculate_dynamic_sl_tp(symbol, signal_type, atr_period=14, atr_multiplier=1.5):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, atr_period + 1)
    if rates is None or len(rates) < atr_period:
        print("⚠️ Not enough data for ATR. Using fixed SL/TP.")
        return (None, None)

    highs = [x['high'] for x in rates]
    lows = [x['low'] for x in rates]
    closes = [x['close'] for x in rates]

    tr_list = [max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1])) for i in range(1, len(rates))]
    atr = sum(tr_list) / len(tr_list)

    sl_distance = atr * atr_multiplier
    tp_distance = atr * atr_multiplier * 1.5

    current_price = mt5.symbol_info_tick(symbol).ask if signal_type == "BUY" else mt5.symbol_info_tick(symbol).bid
    sl = current_price - sl_distance if signal_type == "BUY" else current_price + sl_distance
    tp = current_price + tp_distance if signal_type == "BUY" else current_price - tp_distance

    return round(sl, 2), round(tp, 2)

# === Execute Trade ===
def place_trade(signal):
    # ✅ Check if trade is already active
    try:
        with open("trade_status.txt", "r") as f:
            status = f.read().strip()
            if status == "OPEN":
                print("⚠ Cannot place trade — previous trade still open.")
                return False
    except FileNotFoundError:
        # If file missing, create and assume CLOSED
        with open("trade_status.txt", "w") as f:
            f.write("CLOSED")

    config = load_config()
    symbol = config["mt5"]["symbol"]
    lot_size = config["strategy"]["lot_size"]
    signal_type = signal["signal"].upper()

    order_type = mt5.ORDER_TYPE_BUY if signal_type == "BUY" else mt5.ORDER_TYPE_SELL
    price = mt5.symbol_info_tick(symbol).ask if signal_type == "BUY" else mt5.symbol_info_tick(symbol).bid

    sl, tp = calculate_dynamic_sl_tp(symbol, signal_type)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 123456,
        "comment": "BTC_SCALPING",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ Trade failed: {result.retcode} - {result.comment}")
        return False

    print(f"✅ Trade executed: {signal_type} at {price}")

    # ✅ Mark trade status as OPEN
    with open("trade_status.txt", "w") as f:
        f.write("OPEN")

    signal.update({
        "type": signal_type.lower(),
        "price": price,
        "volume": lot_size,
        "sl": sl,
        "tp": tp,
        "entry_price": price,
        "exit_price": mt5.symbol_info_tick(symbol).bid if signal_type == "BUY" else mt5.symbol_info_tick(symbol).ask,
    })

    log_trade(signal)
    return True


# === Monitor Closed Trades ===
def track_closed_trades():
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = f"logs/trades_{today}.csv"
    config = load_config()
    symbol = config["mt5"]["symbol"]
    lot_size = config["strategy"]["lot_size"]

    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        return

    if "closed" not in df.columns:
        df["closed"] = False
    if "close_price" not in df.columns:
        df["close_price"] = np.nan
    if "profit" not in df.columns:
        df["profit"] = np.nan
    if "close_time" not in df.columns:
        df["close_time"] = pd.NaT

    df_open = df[df["closed"] != True]
    if df_open.empty:
        return

    deals = mt5.history_deals_get(datetime.now() - timedelta(days=1), datetime.now())
    if deals is None:
        return

    for i, row in df_open.iterrows():
        for d in deals:
            if (
                d.symbol == symbol and
                round(d.volume, 2) == round(lot_size, 2) and
                d.comment.startswith("BTC_SCALPING") and
                ((row["type"] == "buy" and d.type == mt5.DEAL_TYPE_SELL) or
                 (row["type"] == "sell" and d.type == mt5.DEAL_TYPE_BUY))
            ):
                df.loc[i, "closed"] = True
                df.loc[i, "close_price"] = round(d.price, 2)
                df.loc[i, "profit"] = round(d.profit, 2)
                df.loc[i, "close_time"] = pd.to_datetime(datetime.fromtimestamp(d.time))

                print(f"📉 Closed trade logged: {row['type']} at {d.price} (P&L: ${d.profit:.2f})", flush=True)
                
                # ✅ Fix: Correct arguments for summary
                try:
                    entry_price = float(row.get("price", row.get("entry_price", 0)))
                except:
                    entry_price = float(row['entry_price'])  # fallback if needed
                exit_price = round(d.price, 2)
                lot = float(row.get("volume", lot_size))
                profit = float(d.profit)
                result = "WIN" if d.profit > 0 else "LOSE"
                record_trade_summary(
                    symbol=symbol,
                    direction=row["type"].upper(),
                    entry_price=entry_price,
                    exit_price=exit_price,
                    lot=lot,
                )


                try:
                    # Load recent candles
                    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 50)
                    df_candles = pd.DataFrame(rates)
                    df_candles['time'] = pd.to_datetime(df_candles['time'], unit='s')
                    df_candles = add_indicators(df_candles)

                    # Align with entry time
                    entry_time = pd.to_datetime(row["time"]) if "time" in row else df_candles["time"].iloc[-20]
                    entry_index = df_candles[df_candles["time"] <= entry_time].index.max()
                    trade_type = row["type"].upper()
                    result = "WIN" if d.profit > 0 else "LOSS"

                    # Extract and save pattern
                    pattern_features = extract_pattern_features(df_candles, entry_index, trade_type, result)
                    print("🧠 Pattern Features Extracted:", pattern_features)
                    save_pattern_memory(pattern_features)
                    print("✅ Pattern saved to pattern_memory.csv")

                except Exception as e:
                    print(f"⚠️ Error saving pattern memory: {e}", flush=True)

                break  # stop after matching one deal

        # Update trade status if no open position
        positions = mt5.positions_get(symbol=symbol)
        if not positions or len(positions) == 0:
            with open("trade_status.txt", "w") as f:
                f.write("CLOSED")

    df.to_csv(filepath, index=False)





# === Daily Summary ===
def print_daily_summary():
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = f"logs/trades_{today}.csv"

    try:
        df = pd.read_csv(filepath)

        # Ensure required columns exist
        if "closed" not in df.columns or "profit" not in df.columns:
            print("⚠️ Incomplete trade log data.")
            return

        closed_trades = df[df["closed"] == True]
        total_pnl = closed_trades["profit"].sum()
        num_trades = len(closed_trades)

        print(f"📊 Today's Realized PnL: ${total_pnl:.2f} from {num_trades} trades.")

    except FileNotFoundError:
        print("📁 No trade file found for today.")
    except Exception as e:
        print(f"⚠️ Error printing summary: {str(e)}")

# === Market Snapshot for Logging ===
def get_market_snapshot():
    symbol = "BTCUSDm"
    timeframe = mt5.TIMEFRAME_M1
    bars = mt5.copy_rates_from_pos(symbol, timeframe, 0, 10)

    if bars is None or len(bars) == 0:
        return "ERROR: Unable to fetch market data from MT5"

    snapshot = f"Last 10 candles for {symbol}:\n"
    for bar in bars:
        time_str = datetime.fromtimestamp(bar['time']).strftime('%Y-%m-%d %H:%M:%S')
        snapshot += f"{time_str} | O: {bar['open']} H: {bar['high']} L: {bar['low']} C: {bar['close']} Vol: {bar['tick_volume']}\n"
    return snapshot

# === MAIN LOOP ===
if __name__ == "__main__":
    connect_mt5()

    # Load memory for learning filter
    if os.path.exists('data/pattern_memory.csv'):
        pattern_memory_df = pd.read_csv('data/pattern_memory.csv')
    else:
        pattern_memory_df = pd.DataFrame()

    if is_risk_exceeded():
        print("❌ Risk exceeded. Skipping all trades.")
    else:
        signal = get_trade_signal()
        if signal:
            print(f"📈 Signal: {signal}")
            config = load_config()
            symbol = config["mt5"]["symbol"]

            # Get 50 recent M1 candles for pattern matching
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 50)
            if rates is None:
                print("⚠️ Market data fetch failed — skipping trade.")
            else:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df = add_indicators(df)

                entry_index = len(df) - 1  # Save which candle was used for pattern
                pattern_features = extract_pattern_features(df, len(df)-1, signal["signal"].upper(), result="PENDING")
                is_good_pattern = is_pattern_profitable(pattern_features, pattern_memory_df)

                if not is_good_pattern:
                    print("[🚫] Pattern rejected by memory — trade skipped.")
                else:
                    success = place_trade(signal)
                    if not success:
                        print("⚠️ Trade execution failed.")
        else:
            print("⏸️ No valid signal at this moment.")

    track_closed_trades()
    print_daily_summary()
