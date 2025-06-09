import MetaTrader5 as mt5

# Initialize connection
if not mt5.initialize():
    print("❌ Initialization failed:", mt5.last_error())
    quit()

# Get all available symbols
symbols = mt5.symbols_get()

print("✅ Available Symbols on Your MT5 Account:\n")
for symbol in symbols:
    print(symbol.name)

mt5.shutdown()
