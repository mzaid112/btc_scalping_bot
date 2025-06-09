# strategy_engine.py
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import json
from datetime import datetime
import os

LAST_SIGNAL_FILE = "logs/last_signal.txt"


def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def get_btc_data(timeframe, bars=100):
    tf_map = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5
    }
    SYMBOL = "BTCUSDm"  # Replace with exact name from MT5
    rates = mt5.copy_rates_from_pos(SYMBOL, tf_map[timeframe], 0, bars)

    
    if rates is None or len(rates) == 0:
        print("⚠️ Error: No data received from MT5. Check if BTCUSD is open and connected.")
        return None

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df


def calculate_indicators(df):
    df["EMA7"] = df["close"].ewm(span=7).mean()
    df["EMA21"] = df["close"].ewm(span=21).mean()
    df["ATR"] = df["high"] - df["low"]
    df["ATR"] = df["ATR"].rolling(window=14).mean()
    return df

def generate_signal(df):
    latest = df.iloc[-1]
    previous = df.iloc[-2]

    signal = None
    reason = ""

    if previous["EMA7"] < previous["EMA21"] and latest["EMA7"] > latest["EMA21"]:
        signal = "buy"
        reason = "EMA7 crossed above EMA21"
    elif previous["EMA7"] > previous["EMA21"] and latest["EMA7"] < latest["EMA21"]:
        signal = "sell"
        reason = "EMA7 crossed below EMA21"

    return signal, latest["close"], latest["ATR"], reason

def get_trade_signal():
    config = load_config()
    df = get_btc_data(config["strategy"]["timeframe"])

    if df is None:
        return None

    df = calculate_indicators(df)
    signal, entry_price, atr, reason = generate_signal(df)

    if signal:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Prevent duplicate signal
        if os.path.exists(LAST_SIGNAL_FILE):
            with open(LAST_SIGNAL_FILE, "r") as f:
                last_time = f.read().strip()
            if last_time == current_time:
                return None  # Same signal already acted on

        # Save new signal time
        with open(LAST_SIGNAL_FILE, "w") as f:
            f.write(current_time)

        sl = config["strategy"]["sl_atr_multiplier"] * atr
        tp = config["strategy"]["tp_atr_multiplier"] * atr
        return {
            "signal": signal,
            "entry_price": round(entry_price, 2),
            "stop_loss": round(sl, 2),
            "take_profit": round(tp, 2),
            "reason": reason,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    return None


# Optional test
if __name__ == "__main__":
    if not mt5.initialize():
        raise RuntimeError("MT5 init failed")
    signal = get_trade_signal()
    if signal:
        print("📈 Signal:", signal)
    else:
        print("No trade signal at this time.")
