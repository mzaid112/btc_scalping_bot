from pattern_logger import log_pattern_memory

# Dummy indicators like RSI, EMA, MACD, etc.
dummy_indicators = {
    "rsi": 62.3,
    "ema_fast": 10550.2,
    "ema_slow": 10520.9,
    "macd": 4.2,
    "macd_signal": 2.5,
    "volume": 2394,
}

# Simulate a winning trade with indicators
log_pattern_memory("BUY", "WIN", dummy_indicators)
