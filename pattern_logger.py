import pandas as pd
import os
from datetime import datetime

PATTERN_FILE = "data/pattern_memory.csv"

def log_pattern_memory(direction, result, indicators):
    if not indicators:
        return

    pattern_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "direction": direction,
        "result": result,  # WIN or LOSS
    }

    # Include all indicators
    pattern_entry.update(indicators)

    df = pd.DataFrame([pattern_entry])

    write_header = not os.path.exists(PATTERN_FILE)
    df.to_csv(PATTERN_FILE, mode='a', index=False, header=write_header)

    print(f"🧠 Pattern memory updated: {result} | {direction} | Indicators: {list(indicators.keys())}")
