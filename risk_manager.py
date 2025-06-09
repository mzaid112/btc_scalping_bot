# risk_manager.py
import pandas as pd
import os
from datetime import datetime
from configparser import ConfigParser
from utils.helpers import read_notes_file  # ✅ Already present


def get_daily_stats():
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = f"logs/trades_{today}.csv"

    if not os.path.exists(log_file):
        return {
            "total_trades": 0,
            "total_profit": 0,
            "total_loss": 0,
            "net_pl": 0,
            "capital": 10  # Assume default if not configured
        }

    df = pd.read_csv(log_file)

    profit = 0
    loss = 0

    for _, row in df.iterrows():
        try:
            pl = float(row["pnl"])
            if pl >= 0:
                profit += pl
            else:
                loss += abs(pl)
        except:
            continue

    net_pl = profit - loss

    # --- Load capital from config or assume default
    config_path = "config.json"
    capital = 1000
    if os.path.exists(config_path):
        import json
        with open(config_path, "r") as f:
            conf = json.load(f)
            capital = conf.get("account", {}).get("daily_start_balance", 1000)

    return {
        "total_trades": len(df),
        "total_profit": profit,
        "total_loss": loss,
        "net_pl": net_pl,
        "capital": capital
    }

def is_risk_exceeded():
    # ✅ 1. Check notes.txt for manual trade block
    notes = read_notes_file()
    if "DO NOT TRADE" in notes or "BLOCK ALL TRADES" in notes:
        print("🚫 Trade blocked by notes.txt instruction.")
        return True

    # ✅ 2. Check drawdown-based risk
    stats = get_daily_stats()
    capital = stats["capital"]
    profit = stats["total_profit"]
    loss = stats["total_loss"]

    #calculate PnL
    net_profit = profit - loss

    #calculate drawdawn
    drawdown = -net_profit / capital

    if drawdown >=0.20:
        print(f"🚫 Risk limit hit: {drawdown*100:.0f}% drawdown on capital.")
        return True
    
    return False
