import pandas as pd

def clean_trade_log(file):
    try:
        df = pd.read_csv(file, on_bad_lines='skip')  # skip malformed rows
        df.to_csv(file, index=False)
        print("✅ Cleaned malformed rows in trade log.")
    except Exception as e:
        print(f"⚠️ Failed to clean trade log: {e}")

clean_trade_log("trade_log.csv")
