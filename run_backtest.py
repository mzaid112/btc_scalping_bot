from backtest_engine import fetch_recent_data, simulate_backtest, save_backtest_results

df = fetch_recent_data()
trades = simulate_backtest(df)
save_backtest_results(trades)
