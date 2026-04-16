import os
import hashlib
import base64
import argparse
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PRIV_KEY_PATH = os.path.join(SCRIPT_DIR, '../data/ota_priv.pem')
DEFAULT_FW_PATH = os.path.join(SCRIPT_DIR, '../.pio/build/dht_bmp/firmware.bin')

def sign_firmware(fw_path=DEFAULT_FW_PATH):
    # 1. Load Private Key
    if not os.path.exists(PRIV_KEY_PATH):
        print(f"[-] Error: Private key not found at {PRIV_KEY_PATH}")
        print("    Run 'python generate_keys.py' first.")
        return

    with open(PRIV_KEY_PATH, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None
        )

    # 2. Check Firmware exists & Calculate SHA256
    if not os.path.exists(fw_path):
        print(f"[-] Error: Firmware not found at {fw_path}")
        print("    Did you run 'Build' in PlatformIO?")
        return

    with open(fw_path, "rb") as f:
        fw_data = f.read()
        
        # ESP-IDF 'esptool' builds append the true App Image SHA-256 hash 
        # to the very end of the firmware.bin file (last 32 bytes) if the 
        # hash_appended flag (byte 23) is set to 1.
        if len(fw_data) > 32 and fw_data[23] == 1:
            sha256_hex = fw_data[-32:].hex()
        else:
            # Fallback if standard ESP32 format wasn't used
            sha256_hex = hashlib.sha256(fw_data).hexdigest()

    print(f"[*] Firmware: {fw_path}")
    print(f"[*] Size:     {len(fw_data)} bytes")
    print(f"[*] SHA256:   {sha256_hex}")

    # 3. Sign the SHA256 hash string directly
    # The ESP32 will verify: RSA_Verify(sha256_hex, signature, public_key)
    signature = private_key.sign(
        sha256_hex.encode('utf-8'),
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    signature_b64 = base64.b64encode(signature).decode('utf-8')

    # 4. Output — paste these into the HydroponicOne Dashboard OTA page
    print("\n" + "="*60)
    print(" SIGNED OTA CREDENTIALS — Paste into HydroponicOne Dashboard")
    print("="*60)
    print(f"\n  SHA256:    {sha256_hex}")
    print(f"\n  Signature: {signature_b64}")
    print("\n" + "="*60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sign ESP32 Firmware for Secure OTA",
        epilog="Example:\n  python sign_firmware.py\n  python sign_firmware.py --bin .pio/build/dht_bmp/firmware.bin",
        formatter_class=argparse.RawTextHelpFormatter
        )
    parser.add_argument("--bin", default=DEFAULT_FW_PATH, help="Path to firmware.bin (default: auto-detect from .pio)")
    
    args = parser.parse_args()
    sign_firmware(args.bin)