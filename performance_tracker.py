# performance_tracker.py

import pandas as pd
import os
from datetime import datetime

def summarize_daily_performance():
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = f"logs/trades_{today}.csv"

    if not os.path.exists(filepath):
        return "No trades today."

    df = pd.read_csv(filepath)

    total_trades = len(df)
    total_pnl = df["pnl"].sum()
    avg_pnl = df["pnl"].mean()
    wins = df[df["pnl"] > 0].shape[0]
    losses = df[df["pnl"] < 0].shape[0]
    win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0

    summary = f"""
📊 Daily Performance Summary ({today})
-----------------------------
Total Trades: {total_trades}
Wins: {wins}
Losses: {losses}
Win Rate: {win_rate:.2f}%
Total PnL: {total_pnl:.2f}
Average PnL: {avg_pnl:.2f}
-----------------------------
"""
    return summary

if __name__ == "__main__":
    print(summarize_daily_performance())

def track_closed_trades():
    # You can enhance this later to track SL/TP hits etc.
    print("📊 track_closed_trades() called (not yet implemented)")
