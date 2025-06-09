import MetaTrader5 as mt5
import pandas as pd

# Connect to MT5
if not mt5.initialize():
    print("❌ MT5 initialization failed")
    mt5.shutdown()
    quit()

# Set the symbol and timeframe
symbol = "BTCUSDm"
timeframe = mt5.TIMEFRAME_M1
count = 10

# Try fetching the last 10 candles
rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)

if rates is None or len(rates) == 0:
    print("❌ Failed to fetch data. Check symbol/timeframe.")
else:
    df = pd.DataFrame(rates)
    print("✅ Data fetched successfully:")
    print(df.tail())

mt5.shutdown()
