import os
import numpy as np
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime
import matplotlib.pyplot as plt
import csv
import ast  # ADD THIS AT TOP IF MISSING
from config import SYMBOL
from pattern_logger import log_pattern_memory
from learning_agents.pattern_utils import extract_pattern_features
from learning_agent import save_pattern_memory



# Ensure the directory exists
os.makedirs("data", exist_ok=True)

# Path for pattern memory
PATTERN_MEMORY_FILE = "data/pattern_memory.csv"

# ✅ Create pattern memory file if it doesn't exist
if not os.path.exists(PATTERN_MEMORY_FILE):
    df = pd.DataFrame(columns=[
        "timestamp", "signal", "result", "last_3_highs", "last_3_lows",
        "ema_20", "rsi", "macd", "pattern"
    ])
    df.to_csv(PATTERN_MEMORY_FILE, index=False)

LOG_FILE = "data/performance_summary.csv"

# Create file if not exist
if not os.path.exists(LOG_FILE):
    df = pd.DataFrame(columns=[
        "timestamp", "symbol", "direction", "entry_price", "exit_price", "profit", "pips", "lot", "sl_hit", "tp_hit"
    ])
    df.to_csv(LOG_FILE, index=False)



LOG_FILE = "trades_log.csv"



def record_trade_summary(symbol, direction, entry_price, exit_price, lot, sl_hit=False, tp_hit=False, indicators=None):
    profit = (exit_price - entry_price) * lot * (1 if direction == "BUY" else -1)
    pips = (exit_price - entry_price) * (1 if direction == "BUY" else -1)

    summary = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": symbol,
        "direction": direction,
        "entry_price": round(entry_price, 2),
        "exit_price": round(exit_price, 2),
        "profit": round(profit, 2),
        "pips": round(pips, 2),
        "lot": lot,
        "sl_hit": sl_hit,
        "tp_hit": tp_hit
    }

    # ✅ Pattern Memory Logging (Optional)
    if indicators:
        result = "WIN" if profit > 0 else "LOSS"
        log_pattern_memory(direction, result, indicators)


        try:
            features = extract_pattern_features(indicators, direction, result)
            save_pattern_memory(features)
        except Exception as e:
            print(f"[⚠️] Pattern save error: {e}")

    # ✅ Save to correct summary file (NOT trades_log.csv)
    df = pd.DataFrame([summary])
    write_header = not os.path.exists("data/performance_summary.csv")
    df.to_csv("data/performance_summary.csv", mode='a', index=False, header=write_header)

    print(f"💾 Trade summary logged: {summary}")

    try:
        update_daily_summary()
    except Exception as e:
        print(f"⚠️ Error updating daily summary: {e}")

    log_to_trades_log(summary)  # <- put this outside the try/except






def print_pnl_summary():
    try:
        df = pd.read_csv("data/performance_summary.csv")

        total_trades = len(df)
        total_pnl = df["profit"].sum()  # ✅ changed from 'pnl' to 'profit'
        wins = len(df[df["profit"] > 0])
        losses = len(df[df["profit"] < 0])
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
        avg_pnl = df["profit"].mean()

        print("\n📊 === PnL Summary ===")
        print(f"Total Trades     : {total_trades}")
        print(f"Total PnL        : {total_pnl:.2f} USD")
        print(f"Wins             : {wins}")
        print(f"Losses           : {losses}")
        print(f"Win Rate         : {win_rate:.2f}%")
        print(f"Avg Profit/Loss  : {avg_pnl:.2f} USD")
        print("======================\n")

    except Exception as e:
        print(f"⚠️ Error printing summary: {e}")


def update_daily_summary():
    try:
        df = pd.read_csv("data/performance_summary.csv")

        # Group by date
        df["date"] = pd.to_datetime(df["timestamp"]).dt.date
        daily_stats = df.groupby("date").agg(
            total_trades=pd.NamedAgg(column="profit", aggfunc="count"),
            wins=pd.NamedAgg(column="profit", aggfunc=lambda x: (x > 0).sum()),
            losses=pd.NamedAgg(column="profit", aggfunc=lambda x: (x < 0).sum()),
            win_rate=pd.NamedAgg(column="profit", aggfunc=lambda x: (x > 0).sum() / len(x) * 100),
            total_pnl=pd.NamedAgg(column="profit", aggfunc="sum"),
            avg_pnl=pd.NamedAgg(column="profit", aggfunc="mean"),
        ).reset_index()

        # Save to new file
        daily_stats.to_csv("data/daily_summary.csv", index=False)
        print("📅 Daily summary updated.")

    except Exception as e:
        print(f"⚠️ Error updating daily summary: {e}")

def plot_equity_curve():
    try:
        df = pd.read_csv("data/performance_summary.csv")
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["equity"] = df["profit"].cumsum()

        plt.figure(figsize=(10, 5))
        plt.plot(df["timestamp"], df["equity"], label="Equity Curve", color="blue")
        plt.xlabel("Time")
        plt.ylabel("Equity (USD)")
        plt.title("Equity Curve Over Time")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"⚠️ Failed to plot equity curve: {e}")

def plot_pnl_per_trade():
    try:
        df = pd.read_csv("data/performance_summary.csv")
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        plt.figure(figsize=(10, 5))
        colors = df["profit"].apply(lambda x: "green" if x > 0 else "red")
        plt.bar(df["timestamp"], df["profit"], color=colors)
        plt.xlabel("Time")
        plt.ylabel("PnL (USD)")
        plt.title(" PnL Per Trade")
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"⚠️ Failed to plot PnL per trade: {e}")

def plot_daily_summary():
    try:
        df = pd.read_csv("data/daily_summary.csv")
        df["date"] = pd.to_datetime(df["date"])

        plt.figure(figsize=(10, 5))
        plt.bar(df["date"], df["total_pnl"], color="purple")
        plt.xlabel("Date")
        plt.ylabel("Daily PnL (USD)")
        plt.title(" Daily PnL Summary")
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"⚠️ Failed to plot daily summary: {e}")


def log_pattern_memory(signal, result, indicators):
    file_path = "data/pattern_memory.csv"
    file_exists = os.path.exists(file_path)

    with open(file_path, mode="a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["timestamp", "signal", "result", "ema_20", "rsi", "macd", "volume"])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            signal,
            result,
            indicators.get("ema_20", ""),
            indicators.get("rsi", ""),
            indicators.get("macd", ""),
            indicators.get("volume", "")
        ])

def get_recent_indicators(symbol=SYMBOL, timeframe=mt5.TIMEFRAME_M1, count=20):
    if not mt5.initialize():
        raise RuntimeError("❌ Failed to initialize MT5. Check if terminal is running.")


    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        print(f"❌ Failed to get rates for symbol={symbol}, timeframe={timeframe}, count={count}")
        raise ValueError("❌ MT5 failed to fetch data. Check connection or symbol/timeframe.")


    df = pd.DataFrame(rates)

    # Ensure expected columns exist
    expected_columns = ["time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume"]
    if not all(col in df.columns for col in expected_columns):
        df.columns = expected_columns  # Just in case they’re missing

    # Debug print
    print("📊 DEBUG: DataFrame Columns =>", df.columns.tolist())
    print(df.tail())

    highs = list(df["high"].tail(3).values)
    lows = list(df["low"].tail(3).values)
    ema20 = df["close"].ewm(span=20).mean().iloc[-1]

    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    macd_line = df["close"].ewm(span=12).mean() - df["close"].ewm(span=26).mean()

    return {
        "last_3_highs": [round(h, 2) for h in highs],
        "last_3_lows": [round(l, 2) for l in lows],
        "ema_20": round(ema20, 2),
        "rsi": round(rsi.iloc[-1], 2),
        "macd": round(macd_line.iloc[-1], 2),
        "pattern": detect_candle_pattern(df)
    }


def detect_candle_pattern(df):
    """
    A very basic candlestick pattern detector.
    Returns: string name of pattern if detected, else ''
    """

    if len(df) < 3:
        return ""

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    # Example: Bullish Engulfing
    if (previous['close'] < previous['open'] and
        latest['close'] > latest['open'] and
        latest['close'] > previous['open'] and
        latest['open'] < previous['close']):
        return "Bullish Engulfing"

    # Example: Bearish Engulfing
    if (previous['close'] > previous['open'] and
        latest['close'] < latest['open'] and
        latest['open'] > previous['close'] and
        latest['close'] < previous['open']):
        return "Bearish Engulfing"

    return ""  # No pattern detected



def log_to_trades_log(summary):
    log_path = "trades_log.csv"
    df = pd.DataFrame([summary])
    write_header = not os.path.exists(log_path)
    df.to_csv(log_path, mode='a', index=False, header=write_header)


def log_trade(trade_data):
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = f"logs/trades_{today}.csv"

    df = pd.DataFrame([trade_data])
    file_exists = os.path.exists(filepath)

    df.to_csv(filepath, mode='a', header=not file_exists, index=False)
    print(f"📝 Trade logged in {filepath}", flush=True)
    print("📩 Logging trade data:", trade_data, flush=True)

