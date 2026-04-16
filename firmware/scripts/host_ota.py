import os
import ssl
import socket
import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(SCRIPT_DIR, '../data/ota_ca.pem')
KEY_FILE = os.path.join(SCRIPT_DIR, 'ota_ca_key.pem')


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'
    finally:
        s.close()


def start_server(port, directory):
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        print("[-] Error: Missing HTTPS certificates.")
        print(f"    Expected cert: {CERT_FILE}")
        print(f"    Expected key:  {KEY_FILE}")
        print("\n    Run first: python generate_keys.py --ip <your-local-ip>")
        return

    # Expand and validate directory
    directory = os.path.realpath(directory)
    if not os.path.isdir(directory):
        print(f"[-] Error: Directory not found: {directory}")
        print("    Did you build the firmware? Run: pio run -e dht_bmp")
        return

    # Detect which IP is embedded in the cert for helpful display
    local_ip = get_local_ip()

    os.chdir(directory)

    httpd = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    firmware_url = f"https://{local_ip}:{port}/firmware.bin"

    print("=" * 60)
    print("  HydroponicOne Local HTTPS OTA Server")
    print("=" * 60)
    print(f"  Serving:   {directory}")
    print(f"  Firmware URL (use this in dashboard):")
    print(f"    {firmware_url}")
    print()
    print("  ⚠  If the IP above is wrong (VPN / Docker), regenerate:")
    print("       python generate_keys.py --ip <correct-ip> --regen-ca")
    print("  Then re-flash LittleFS and restart this server.")
    print("=" * 60)
    print("[*] Press Ctrl+C to stop.\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopping server...")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="HydroponicOne Local HTTPS OTA Server",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python host_ota.py\n"
            "  python host_ota.py --port 8443\n"
            "  python host_ota.py --dir .pio/build/bme280/\n"
        )
    )
    parser.add_argument("--port", type=int, default=8443,
                        help="Port to listen on (default: 8443)")
    parser.add_argument("--dir",
                        default=os.path.join(SCRIPT_DIR, '../.pio/build/dht_bmp/'),
                        help="Directory to serve firmware from")
    args = parser.parse_args()
    start_server(args.port, args.dir)
