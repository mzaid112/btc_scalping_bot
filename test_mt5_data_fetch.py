import MetaTrader5 as mt5
from config import SYMBOL

if not mt5.initialize():
    raise RuntimeError("❌ MT5 not initialized")

rates = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M1, 0, 5)

if rates is None or len(rates) == 0:
    print("❌ No data received. Check symbol or timeframe.")
else:
    print("✅ Data received:")
    for r in rates:
        print(r)
