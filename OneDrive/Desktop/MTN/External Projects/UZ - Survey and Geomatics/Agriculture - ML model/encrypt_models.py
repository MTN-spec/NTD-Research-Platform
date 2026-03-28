"""
encrypt_models.py
─────────────────────────────────────────────────────────────────────────
One-time script to encrypt ML model files (.pkl) using Fernet
symmetric encryption.

Usage:
    python encrypt_models.py

This will:
  1. Generate a new encryption key (if not already in .env)
  2. Encrypt all .pkl files in the models/ directory
  3. Save encrypted versions as .enc files
  4. Print the key to add to your .env file

The original .pkl files are preserved as backups with a .bak extension.
"""

import os
import sys

try:
    from cryptography.fernet import Fernet
except ImportError:
    print("ERROR: 'cryptography' package not installed.")
    print("Run:  pip install cryptography")
    sys.exit(1)

try:
    from dotenv import load_dotenv, set_key
    load_dotenv()
except ImportError:
    pass

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")


def generate_or_load_key():
    """Generate a new Fernet key or load from environment."""
    existing_key = os.environ.get("MODEL_ENCRYPTION_KEY", "")
    if existing_key:
        print(f"Using existing encryption key from .env")
        return existing_key.encode()
    
    key = Fernet.generate_key()
    print(f"\nGenerated NEW encryption key.")
    print(f"Add this to your .env file:\n")
    print(f'MODEL_ENCRYPTION_KEY="{key.decode()}"')
    print()
    
    # Auto-write to .env if dotenv is available
    try:
        set_key(ENV_FILE, "MODEL_ENCRYPTION_KEY", key.decode())
        print(f"Key automatically saved to {ENV_FILE}")
    except Exception:
        print("Could not auto-save key. Please add it to .env manually.")
    
    return key


def encrypt_file(filepath, cipher):
    """Encrypt a single file and save as .enc"""
    with open(filepath, "rb") as f:
        data = f.read()
    
    encrypted = cipher.encrypt(data)
    enc_path = filepath.replace(".pkl", ".enc")
    
    with open(enc_path, "wb") as f:
        f.write(encrypted)
    
    # Rename original to .bak
    bak_path = filepath + ".bak"
    os.rename(filepath, bak_path)
    
    size_orig = len(data)
    size_enc = len(encrypted)
    
    return enc_path, bak_path, size_orig, size_enc


def main():
    print("=" * 60)
    print("  Optiflow Aqua Systems — Model Encryption Tool")
    print("=" * 60)
    print()
    
    # Find .pkl files
    pkl_files = [f for f in os.listdir(MODEL_DIR) if f.endswith(".pkl")]
    
    if not pkl_files:
        print("No .pkl files found in models/ directory.")
        print("Nothing to encrypt.")
        return
    
    print(f"Found {len(pkl_files)} model files to encrypt:")
    for f in pkl_files:
        size = os.path.getsize(os.path.join(MODEL_DIR, f))
        print(f"  {f} ({size:,} bytes)")
    print()
    
    # Generate or load key
    key = generate_or_load_key()
    cipher = Fernet(key)
    print()
    
    # Encrypt each file
    print("Encrypting models...")
    for filename in pkl_files:
        filepath = os.path.join(MODEL_DIR, filename)
        enc_path, bak_path, size_orig, size_enc = encrypt_file(filepath, cipher)
        print(f"  {filename}")
        print(f"    Encrypted: {os.path.basename(enc_path)} ({size_enc:,} bytes)")
        print(f"    Backup:    {os.path.basename(bak_path)}")
    
    print()
    print("Encryption complete!")
    print()
    print("IMPORTANT:")
    print("  1. The .enc files are encrypted and safe to distribute")
    print("  2. The .bak files are your UNENCRYPTED backups — keep them safe")
    print("  3. The MODEL_ENCRYPTION_KEY in .env is required to run the app")
    print("  4. NEVER share the encryption key publicly")


if __name__ == "__main__":
    main()
