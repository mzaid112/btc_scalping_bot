import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import talib
import os
from learning_agents import save_pattern_memory
from learning_agents import is_pattern_profitable
from learning_agents import extract_pattern_features


def fetch_recent_data(symbol="BTCUSDm", timeframe=mt5.TIMEFRAME_M1, bars=1000):
    if not mt5.initialize():
        raise RuntimeError("MT5 initialization failed")

    now = datetime.now()
    from_time = now - timedelta(minutes=bars)

    rates = mt5.copy_rates_range(symbol, timeframe, from_time, now)
    if rates is None:
        raise RuntimeError("Failed to fetch rates")

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')

    # ✅ Add technical indicators using TA-Lib
    df['ema_20'] = talib.EMA(df['close'], timeperiod=20)
    df['ema_50'] = talib.EMA(df['close'], timeperiod=50)
    df['rsi'] = talib.RSI(df['close'], timeperiod=14)
    df['macd'], df['macdsignal'], df['macdhist'] = talib.MACD(df['close'])

    return df




def calculate_atr(df, period=14):
    df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=period)
    return df

def dummy_llm_signal(candle):
    """Replace this with your LLM/GPT logic later"""
    # Just for testing — randomly returns a trade signal
    return np.random.choice(['BUY', 'SELL', 'NONE'])

def simulate_backtest(df, risk_per_trade_usd=5):
    df = calculate_atr(df)
    trades = []
    position = None

    # ✅ Load pattern memory
    if os.path.exists('data/pattern_memory.csv'):
        memory_df = pd.read_csv('data/pattern_memory.csv')
    else:
        memory_df = pd.DataFrame()

    for i in range(14, len(df) - 1):  # start from 14 for ATR to stabilize
        row = df.iloc[i]
        signal = dummy_llm_signal(row)

        # ✅ Before placing trade, filter based on pattern history
        if position is None and signal in ['BUY', 'SELL']:
            features = extract_pattern_features(df, i, signal, result="PENDING")

            if not is_pattern_profitable(features, memory_df):
                print(f"[⛔] Skipping trade due to low pattern confidence at {df.index[i]}")
                continue

            # ✅ Continue placing trade if pattern is good
            atr = row['atr']
            sl = row['close'] - atr if signal == 'BUY' else row['close'] + atr
            tp = row['close'] + 2 * atr if signal == 'BUY' else row['close'] - 2 * atr

            position = {
                'type': signal,
                'entry_time': row['time'],
                'entry_price': row['close'],
                'sl': sl,
                'tp': tp,
                'open_index': i
            }

        # ✅ Simulate open trade's SL/TP outcome
        elif position is not None:
            next_row = df.iloc[i + 1]

            if position['type'] == 'BUY':
                if next_row['low'] <= position['sl']:
                    exit_price = position['sl']
                    result = 'LOSS'
                elif next_row['high'] >= position['tp']:
                    exit_price = position['tp']
                    result = 'WIN'
                else:
                    continue
            elif position['type'] == 'SELL':
                if next_row['high'] >= position['sl']:
                    exit_price = position['sl']
                    result = 'LOSS'
                elif next_row['low'] <= position['tp']:
                    exit_price = position['tp']
                    result = 'WIN'
                else:
                    continue

            # ✅ Log pattern memory after trade result
            features = extract_pattern_features(df, position['open_index'], signal, result)
            save_pattern_memory(features)

            # ✅ Record trade
            trades.append({
                'entry_time': position['entry_time'],
                'exit_time': next_row['time'],
                'type': position['type'],
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'result': result
            })

            position = None  # Reset after trade is closed

    return trades



def save_backtest_results(trades, filename='data/backtest_results.csv'):
    if not trades:
        print("No trades to save.")
        return

    os.makedirs('data', exist_ok=True)
    df = pd.DataFrame(trades)
    df.to_csv(filename, index=False)
    print(f"[✅] Backtest results saved to {filename}")
