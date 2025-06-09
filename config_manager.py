# config_manager.py
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

def lock_passwords():
    """Turn passwords into secret code"""
    # Generate encryption key
    key = Fernet.generate_key()
    
    # Save key to file
    with open(".key", "wb") as key_file:
        key_file.write(key)
    
    # Create encryptor
    cipher = Fernet(key)
    
    # Get passwords from .env
    secrets = {
        "MT5_PASSWORD": os.getenv("MT5_PASSWORD"),
        "LLM_API_KEYS": os.getenv("LLM_API_KEYS")
    }
    
    # Encrypt passwords
    encrypted = cipher.encrypt(str(secrets).encode())
    
    # Save encrypted passwords
    with open("secrets.enc", "wb") as enc_file:
        enc_file.write(encrypted)
    
    print("🔒 Passwords locked successfully!")

def unlock_passwords():
    """Read secret code when needed"""
    # Load encryption key
    with open(".key", "rb") as key_file:
        key = key_file.read()
        
    # Create decryptor
    cipher = Fernet(key)
    
    # Load encrypted secrets
    with open("secrets.enc", "rb") as enc_file:
        encrypted = enc_file.read()
    
    # Decrypt and return secrets
    return eval(cipher.decrypt(encrypted).decode())