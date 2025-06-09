import pandas as pd
import matplotlib.pyplot as plt


def analyze_backtest_results(csv_path='data/backtest_results.csv'):
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"[❌] File not found: {csv_path}")
        return

    if df.empty:
        print("[❌] No backtest results found.")
        return

    df['pnl'] = df['exit_price'] - df['entry_price']
    df['pnl'] = df.apply(lambda row: row['pnl'] if row['type'] == 'BUY' else -row['pnl'], axis=1)

    total_trades = len(df)
    wins = df[df['pnl'] > 0]
    losses = df[df['pnl'] <= 0]
    
    win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0
    total_pnl = df['pnl'].sum()
    avg_win = wins['pnl'].mean() if not wins.empty else 0
    avg_loss = losses['pnl'].mean() if not losses.empty else 0
    expectancy = df['pnl'].mean()

    print("🔍 Backtest Performance Summary:")
    print(f"🧾 Total Trades      : {total_trades}")
    print(f"✅ Win Rate          : {win_rate:.2f}%")
    print(f"💰 Total PnL         : {total_pnl:.2f}")
    print(f"📈 Avg Win           : {avg_win:.2f}")
    print(f"📉 Avg Loss          : {avg_loss:.2f}")
    print(f"🧠 Expectancy/Trade  : {expectancy:.2f}")

    plot_equity_curve(df)
    generate_daily_summary(df)





def plot_equity_curve(df):
    df['pnl'] = df['exit_price'] - df['entry_price']
    df['pnl'] = df.apply(lambda row: row['pnl'] if row['type'] == 'BUY' else -row['pnl'], axis=1)
    df['equity'] = df['pnl'].cumsum()

    # Use exit_time if available, otherwise use index
    x_axis = pd.to_datetime(df['exit_time']) if 'exit_time' in df.columns else df.index

    plt.figure(figsize=(10, 6))
    plt.plot(x_axis, df['equity'], color='green', linewidth=2)
    plt.title('📈 Backtest Equity Curve')
    plt.xlabel('Time')
    plt.ylabel('Cumulative PnL')
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def generate_daily_summary(df):
    df['date'] = pd.to_datetime(df['entry_time']).dt.date

    df['pnl'] = df['exit_price'] - df['entry_price']
    df['pnl'] = df.apply(lambda row: row['pnl'] if row['type'] == 'BUY' else -row['pnl'], axis=1)
    df['win'] = df['result'] == 'WIN'

    daily_stats = df.groupby('date').agg({
        'entry_time': 'count',
        'win': 'sum',
        'pnl': 'sum'
    }).rename(columns={
        'entry_time': 'total_trades',
        'win': 'wins',
        'pnl': 'total_pnl'
    })

    daily_stats['win_rate'] = (daily_stats['wins'] / daily_stats['total_trades']) * 100
    daily_stats = daily_stats.round(2)

    print("\n📅 Daily Summary:")
    print(daily_stats)

    # Save to CSV
    daily_stats.to_csv("data/performance_summary.csv")
    print("✅ Saved daily summary to → data/performance_summary.csv")
