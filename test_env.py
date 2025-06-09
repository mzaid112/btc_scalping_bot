# test_env.py
import os
from dotenv import load_dotenv

load_dotenv()  # Load our secret file

print("=== Secret Checker ===")
print(f"MT5 Account: {os.getenv('MT5_ACCOUNT_ID')}")
print(f"Password exists: {len(os.getenv('MT5_PASSWORD')) > 0}")
print(f"First 2 letters of password: {os.getenv('MT5_PASSWORD')[:2]}...")
print(f"LLM Keys: {os.getenv('LLM_API_KEYS').split(',')[0][:10]}...")