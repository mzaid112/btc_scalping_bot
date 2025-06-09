# comms_whatsapp.py
import requests
import urllib.parse
import json

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def send_whatsapp_message(message: str):
    config = load_config()
    phone = config["whatsapp"]["phone"]
    apikey = config["whatsapp"]["apikey"]

    url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={urllib.parse.quote(message)}&apikey={apikey}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("✅ WhatsApp message sent")
        else:
            print("❌ Failed to send WhatsApp message")
    except Exception as e:
        print(f"⚠️ WhatsApp error: {e}")
