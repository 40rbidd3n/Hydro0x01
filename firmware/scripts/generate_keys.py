import os
import sys
import socket
import argparse
import datetime
import ipaddress
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes

# Define paths relative to the scripts folder
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '../data')

PUB_KEY_PATH = os.path.join(DATA_DIR, 'ota_pub.pem')
PRIV_KEY_PATH = os.path.join(DATA_DIR, 'ota_priv.pem')
CA_CERT_PATH = os.path.join(DATA_DIR, 'ota_ca.pem')
CA_KEY_PATH = os.path.join(SCRIPT_DIR, 'ota_ca_key.pem')


def generate_keys():
    print("=" * 60)
    print("  [1/2] Generating RSA-2048 keypair for OTA Signing...")
    print("=" * 60)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    os.makedirs(DATA_DIR, exist_ok=True)

    with open(PRIV_KEY_PATH, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    print(f"[+] Signing private key  →  {PRIV_KEY_PATH}")

    with open(PUB_KEY_PATH, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    print(f"[+] Signing public key   →  {PUB_KEY_PATH}")
    print("\n⚠  CRITICAL: 'data/ota_priv.pem' must NEVER be committed to git!\n")


def get_local_ip():
    """Reliably detect outbound local IP on multi-homed machines."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to be reachable — just triggers routing table lookup
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'
    finally:
        s.close()


def generate_ca_cert(force_ip=None, force_regen=False):
    print("=" * 60)
    print("  [2/2] Generating self-signed HTTPS certificate...")
    print("=" * 60)

    if os.path.exists(CA_CERT_PATH) and os.path.exists(CA_KEY_PATH) and not force_regen:
        print(f"[*] HTTPS cert already exists. Use --regen-ca to regenerate.")
        print(f"    {CA_CERT_PATH}")
        return

    # Determine which IP(s) to embed
    auto_ip = get_local_ip()
    server_ip_str = force_ip if force_ip else auto_ip

    if force_ip:
        print(f"[*] Using user-specified IP: {server_ip_str}")
    else:
        print(f"[*] Auto-detected local IP: {server_ip_str}")
        print(f"    (Use --ip <address> if this is wrong, e.g. VPN, Docker)")

    try:
        server_ip = ipaddress.ip_address(server_ip_str)
    except ValueError:
        print(f"[-] Invalid IP address: {server_ip_str}")
        sys.exit(1)

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u"HydroponicOne Local OTA"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"HydroponicOne"),
    ])

    san_entries = [
        x509.DNSName(u"localhost"),
        x509.IPAddress(ipaddress.ip_address('127.0.0.1')),
        x509.IPAddress(server_ip),
    ]

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
        .sign(private_key, hashes.SHA256())
    )

    with open(CA_CERT_PATH, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print(f"\n[+] HTTPS CA cert (flash to ESP32)  →  {CA_CERT_PATH}")

    with open(CA_KEY_PATH, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    print(f"[+] HTTPS server key (local only)   →  {CA_KEY_PATH}")

    print("\n" + "=" * 60)
    print(" NEXT STEPS")
    print("=" * 60)
    print(f" 1. In PlatformIO: 'Build Filesystem Image'")
    print(f" 2. In PlatformIO: 'Upload Filesystem Image'  ← flashes ota_ca.pem")
    print(f" 3. Run the local server:")
    print(f"      python scripts/host_ota.py")
    print(f" 4. Firmware URL to use in dashboard:")
    print(f"      https://{server_ip_str}:8443/firmware.bin")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="HydroponicOne OTA Key Generator",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python generate_keys.py                   # Auto-detect IP\n"
            "  python generate_keys.py --ip 192.168.1.11  # Specify server IP\n"
            "  python generate_keys.py --ip 192.168.1.11 --regen-ca  # Force regen cert\n"
            "  python generate_keys.py --ca-only --ip 192.168.1.11   # Only regen HTTPS cert\n"
        )
    )
    parser.add_argument("--ip", default=None,
                        help="Your computer's local IP that the ESP32 will connect to")
    parser.add_argument("--regen-ca", action="store_true",
                        help="Force regenerate the HTTPS CA certificate even if it exists")
    parser.add_argument("--ca-only", action="store_true",
                        help="Only regenerate the HTTPS CA certificate, skip RSA signing keys")
    args = parser.parse_args()

    if not args.ca_only:
        generate_keys()
        print()

    generate_ca_cert(force_ip=args.ip, force_regen=args.regen_ca)