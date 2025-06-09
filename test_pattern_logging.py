from pnl_tracker import get_recent_indicators, log_pattern_memory

# Step 1: Get recent indicators from MT5
indicators = get_recent_indicators()

# Step 2: Simulate a trade outcome and pattern log
signal = "BUY"
result = "WIN"

# Step 3: Log the pattern
log_pattern_memory(signal, result, indicators)

print("✅ Pattern successfully logged.")
