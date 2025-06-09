import pandas as pd
import os
import csv
from datetime import datetime
import numpy as np

MEMORY_FILE = "data/pattern_memory.csv"

def load_pattern_memory():
    try:
        df = pd.read_csv(MEMORY_FILE)
        return df
    except Exception as e:
        print(f"❌ Failed to load memory: {e}")
        return pd.DataFrame()

def evaluate_pattern(indicators):
    memory = load_pattern_memory()
    if memory.empty:
        return {"bias": "UNKNOWN", "confidence": 0.0}

    for col in ['rsi', 'ema_20', 'macd', 'volume']:
        if col not in memory.columns:
            print(f"⚠️ Missing column in memory: {col}")
            return {"bias": "UNKNOWN", "confidence": 0.0}
        memory[col] = pd.to_numeric(memory[col], errors='coerce')

    current = pd.Series(indicators)
    memory['distance'] = memory.apply(
        lambda row: ((row[['rsi', 'ema_20', 'macd', 'volume']] - current[['rsi', 'ema_20', 'macd', 'volume']]) ** 2).sum() ** 0.5,
        axis=1
    )

    k = 10
    nearest = memory.sort_values('distance').head(k)

    win_count = (nearest['result'] == 'WIN').sum()
    loss_count = (nearest['result'] == 'LOSS').sum()
    total = win_count + loss_count

    if total == 0:
        return {"bias": "UNKNOWN", "confidence": 0.0}

    bias = "FAVORABLE" if win_count > loss_count else "UNFAVORABLE"
    confidence = round(win_count / total, 2)
    print(f"🧠 Pattern Check: Bias={bias}, Confidence={confidence:.2f}")

    return {"bias": bias, "confidence": confidence}


    



# inside learning_agents/pattern_learning.py
def is_pattern_profitable(pattern, df):
    """Check if pattern is profitable, always return True if no memory exists"""
    if df.empty or len(df) < 10:  # Not enough data
        print("✅ No pattern memory - allowing trade")
        return True
        
    try:
        # Your existing pattern check logic
        return (
            pattern["rsi"] is not None
            and pattern["signal"] == "BUY"
            and pattern["result"] == "WIN"
        )
    except KeyError:
        print("⚠️ Pattern missing required fields - allowing trade")
        return True


def save_pattern_memory(pattern_data, path="data/pattern_memory.csv"):
    """
    Append pattern data to memory CSV. Converts Series to dict and ensures safe saving.
    """
    print(f"💾 Attempting to save pattern: {pattern_data}")
    os.makedirs("data", exist_ok=True)
    # Ensure it's a dict, even if it's a Series
    if isinstance(pattern_data, pd.Series):
        pattern_data = pattern_data.to_dict()

    # Add defaults for expected fields (if missing)
    expected_keys = ['signal', 'rsi', 'macd', 'macdsignal', 'macdhist', 'atr', 'result', 'entry_price', 'exit_price']
    for key in expected_keys:
        pattern_data.setdefault(key, None)

    # Save
    try:
        df_new = pd.DataFrame([pattern_data])
        if os.path.exists(path):
            df_existing = pd.read_csv(path)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new
        df_combined.to_csv(path, index=False)
    except Exception as e:
        print(f"⚠️ Error saving pattern memory: {e}")




def log_pattern_memory(pattern):
    try:
        print(f"🧠 Pattern Memory Logged: {pattern.get('signal')} | RSI: {pattern.get('rsi')} | MACD: {pattern.get('macd')} | Result: {pattern.get('result')}")
    except Exception as e:
        print(f"⚠️ Error logging pattern memory: {e}")


def extract_pattern_features(df_candles, index, trade_type, result):
    if index >= len(df_candles):
        return None

    row = df_candles.iloc[index]
    row_dict = row.to_dict()  # ✅ Convert Series to dictionary to safely use .get()

    pattern = {
        "time": row_dict.get("time"),
        "open": row_dict.get("open"),
        "high": row_dict.get("high"),
        "low": row_dict.get("low"),
        "close": row_dict.get("close"),
        "ema_10": row_dict.get("ema_10"),
        "ema_50": row_dict.get("ema_50"),
        "rsi": row_dict.get("rsi"),
        "macd": row_dict.get("macd"),
        "macd_signal": row_dict.get("macd_signal"),
        "bb_upper": row_dict.get("bb_upper"),
        "bb_lower": row_dict.get("bb_lower"),
        "vwap": row_dict.get("vwap"),
        "obv": row_dict.get("obv"),
        "atr": row_dict.get("atr"),  # If you're calculating this
        "signal": trade_type.upper(),
        "result": result
    }
    print("🔍 df_candles columns:", df_candles.columns.tolist())

    return pattern
