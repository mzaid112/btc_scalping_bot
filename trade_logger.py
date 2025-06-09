import csv
from datetime import datetime
import os
import pandas as pd
from pnl_tracker import record_trade_summary


def log_trade(signal):
    
    os.makedirs("data", exist_ok=True)

    log_file = os.path.join("data", "trade_log.csv")
    
    # Extract trade data
    trade_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": signal["signal"],
        "symbol": signal.get("symbol", "BTCUSD"),  # Default if not provided
        "price": signal["price"],
        "volume": signal["volume"],
        "sl": signal.get("sl", ""),
        "tp": signal.get("tp", ""),
        "comment": signal.get("comment", ""),
        "entry_price": signal.get("entry_price", signal["price"]),  # fallback
        "exit_price": signal.get("exit_price", signal["price"]),    # fallback
        "lot": signal.get("lot", signal["volume"]),
        "sl_hit": signal.get("sl_hit", False),
        "tp_hit": signal.get("tp_hit", False),
        "signal_type": signal["signal"],
    }

    # Save to trade_log.csv
    file_exists = os.path.isfile(log_file)
    df = pd.DataFrame([trade_data])
    df.to_csv(log_file, mode='a', header=not file_exists, index=False)

    # Log to PnL Summary Tracker
    try:
        record_trade_summary(
            symbol=trade_data["symbol"],
            direction=trade_data["signal_type"],
            entry_price=float(trade_data["entry_price"]),
            exit_price=float(trade_data["exit_price"]),
            lot=float(trade_data["lot"]),
            sl_hit=bool(trade_data["sl_hit"]),
            tp_hit=bool(trade_data["tp_hit"])
        )
    except Exception as e:
        print(f"⚠️ Error logging to PnL tracker: {e}")
