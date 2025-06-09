# main.py

import time
from datetime import datetime
import threading
from backtest_engine import fetch_recent_data, simulate_backtest
from execution_engine import connect_mt5, place_trade, track_closed_trades, print_daily_summary
from risk_manager import is_risk_exceeded
from llm_agent import get_llm_signal
from utils.helpers import read_notes_file
from execution_engine import current_trade_active  # at the top of main.py

# main.py (add near the top under imports or in __main__)
with open("trade_status.txt", "w") as f:
    f.write("CLOSED")

with open("trade_status.txt", "r") as f:
    print("📋 Starting with trade status:", f.read().strip())


def run_bot_loop():
    print("🚀 Starting Bitcoin Scalping Bot Loop...")
    
    # Connect to MT5 with retries
    for _ in range(3):
        try:
            connect_mt5()
            break
        except Exception as e:
            print(f"⚠️ Connection failed: {e}")
            time.sleep(5)
    else:
        print("❌ FATAL: Could not connect to MT5")
        return
    
    error_count = 0
    max_errors = 5
    
    while True:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n🕒 {now} - Cycle #{error_count+1}")

            # Reset error count if successful cycle
            error_count = 0
            
            # Read manual instructions
            notes = read_notes_file()
            if "STOP" in notes:
                print("🛑 Emergency stop activated by notes.txt")
                break
                
            # Check risk limits
            if is_risk_exceeded():
                print("⛔ Risk limit exceeded - skipping trade")
                time.sleep(30)
                continue
                
            # Get trading signal
            signal = get_llm_signal()
            print(f"🧠 LLM Signal: {signal['signal']} | Confidence: {signal.get('confidence', 0)}")
            
            # Execute trade if valid signal
            if signal["signal"] in ["BUY", "SELL"]:
                print(f"⚡ Executing {signal['signal']} trade")
                success = place_trade(signal)
                if success:
                    print("✅ Trade executed successfully")
                else:
                    print("❌ Trade execution failed")
                    
            # Track closed trades
            track_closed_trades()
            
            # Print daily summary
            print_daily_summary()
            
            # Normal sleep between cycles
            time.sleep(30)
            
        except Exception as e:
            error_count += 1
            print(f"🔥 ERROR #{error_count}: {str(e)}")
            with open("error_log.txt", "a") as f:
                f.write(f"\n[{datetime.now()}] ERROR: {str(e)}")
                
            if error_count >= max_errors:
                print("⛔ MAX ERRORS REACHED - SHUTTING DOWN")
                break
                
            # Wait longer after each error
            time.sleep(10 * error_count)



def background_learning_loop():
    while True:
        try:
            print("🤖 Running background pattern training...")
            df = fetch_recent_data(bars=500)
            simulate_backtest(df)
        except Exception as e:
            print(f"[⚠️] Background learning error: {e}")
        time.sleep(60 * 5)


if __name__ == "__main__":
    threading.Thread(target=background_learning_loop, daemon=True).start()

    try:
        run_bot_loop()
    except Exception as e:
        print("❌ Bot crashed due to error:", str(e))
        with open("error_log.txt", "a") as f:
            f.write(f"\n[ERROR] {str(e)}")
