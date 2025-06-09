import os
import pandas as pd
from datetime import datetime

# Paths to CSV files
pnl_log_path = "logs/pnl_log.csv"
pattern_log_path = "logs/pattern_memory.csv"

# Define correct headers
pnl_headers = [
    "timestamp", "symbol", "direction", "entry_price", "exit_price",
    "profit", "pips", "lot", "sl_hit", "tp_hit"
]

pattern_headers = [
    "timestamp", "symbol", "direction", "entry_price", "reason", "indicators"
]

# Delete and recreate a file with headers
def reset_csv(path, headers):
    if os.path.exists(path):
        os.remove(path)
        print(f"🗑 Deleted corrupted file: {path}")
    else:
        print(f"📁 No existing file to delete: {path}")
    df = pd.DataFrame(columns=headers)
    df.to_csv(path, index=False)
    print(f"✅ Created new clean file: {path}")

# Run the resets
reset_csv(pnl_log_path, pnl_headers)
reset_csv(pattern_log_path, pattern_headers)
