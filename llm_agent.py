from config_manager import unlock_passwords
secrets = unlock_passwords()

import google.generativeai as genai
import os
from execution_engine import get_market_snapshot
from datetime import datetime
import json
import time
from config_manager import unlock_passwords
secrets = unlock_passwords()

#load api key
with open("config.json") as f:
    config = json.load(f)

    api_keys = secrets["LLM_API_KEYS"].split(',')
    current_key_index = 0


def configure_model(index):
    global model
    genai.configure(api_key=api_keys[index])
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    print(f"🔑 Using API Key #{index + 1}")

# Initially configure with the first key
configure_model(current_key_index)



print("🤖 LLM Agent Activated")



def get_notes():
    try:
        with open("notes.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def build_prompt(market_data, notes):
    prompt = f"""
You are a professional crypto scalper AI operating on 1-minute BTC/USDT charts with high precision.

📅 Current Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 Market Snapshot:
{market_data}

📝 Human Notes & Instructions:
{notes}

🎯 Decision Guidelines:
- Analyze recent price action, trends, volume, and volatility.
- Factor in ATR for price noise filtering.
- Detect breakout or reversal patterns based on candle structures.
- Avoid overtrading; only trade when risk-reward is favorable.
- Never guess. Act only if confident based on current data.

🧠 Think Step-by-Step:
1. What's the recent price behavior? (trend/sideways/spike)
2. How is volume behaving relative to recent candles?
3. Are there support/resistance levels being tested or broken?
4. Is ATR showing low or high volatility?
5. Is it safe to trade, or better to wait?

📌 Return your decision in this format **exactly**:
---
SIGNAL: BUY / SELL / DO_NOT_TRADE  
ENTRY: <Exact number like 105123.45 — do NOT write N/A or text>  
STOP_LOSS: <Exact number — never write N/A>  
TAKE_PROFIT: <Exact number — never write N/A>
REASON: <Short, clear reasoning based on data>
---

"""
    return prompt

def safe_float(value, default=0.0):
    try:
        return float(value.strip())
    except:
        return default


def get_llm_signal():
    api_keys = secrets["LLM_API_KEYS"].split(',')
    print("✅ Connected to MT5")
    
    market_data = get_market_snapshot()
    notes = get_notes()
    prompt = build_prompt(market_data, notes)

    global current_key_index

    while current_key_index < len(api_keys):
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()

            # Parse output
            signal_line = next((line for line in text.splitlines() if "SIGNAL" in line), "SIGNAL: DO_NOT_TRADE")
            reason_line = next((line for line in text.splitlines() if "REASON" in line), "REASON: No reason given")
            entry_line = next((line for line in text.splitlines() if "ENTRY" in line), "ENTRY: 0")
            sl_line = next((line for line in text.splitlines() if "STOP_LOSS" in line), "STOP_LOSS: 0")
            tp_line = next((line for line in text.splitlines() if "TAKE_PROFIT" in line), "TAKE_PROFIT: 0")

            entry_price = safe_float(entry_line.split(":")[-1])
            stop_loss = safe_float(sl_line.split(":")[-1])
            take_profit = safe_float(tp_line.split(":")[-1])

            signal = signal_line.split(":")[-1].strip().upper()
            reason = reason_line.split(":")[-1].strip()

            print(f"🧠 LLM SIGNAL: {signal} | Reason: {reason}")

            return {
                "signal": signal,
                "reason": reason,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
            }

        except Exception as e:
            print(f"⚠️ API Key #{current_key_index + 1} failed: {str(e)}")

            if "ResourceExhausted" in str(e) or "quota" in str(e):
                current_key_index += 1
                if current_key_index < len(api_keys):
                    print("🔁 Switching to next available Gemini API key...")
                    configure_model(current_key_index)
                    time.sleep(1)
                else:
                    print("❌ All Gemini API keys exhausted.")
                    return {
                        "signal": "DO_NOT_TRADE",
                        "reason": "All Gemini API keys exhausted for today.",
                        "entry_price": 0,
                        "stop_loss": 0,
                        "take_profit": 0,
                    }
            else:
                raise  # Other errors should not be silently passed