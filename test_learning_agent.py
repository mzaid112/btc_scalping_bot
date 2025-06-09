from learning_agents import is_pattern_profitable

sample = {
    'ema_20': 10580,
    'rsi': 62,
    'macd': 4.5,
    'volume': 2394
}

result = is_pattern_profitable(sample)
print(f"🧪 Pattern profitable? {result}")
