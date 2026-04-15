# Security & OTA Firmware Updates

HydroponicOne is built for production environments where security and reliability are paramount. This guide explains how to enable firmware signing and manage secure Over-The-Air (OTA) updates.

## 🛠️ Security Configuration

To lock down your system, enable strict security in `firmware/include/config.h`.

### Enforce Strict Security
Uncomment the following line in `config.h`:
```cpp
#define ENFORCE_STRICT_SECURITY
```

**What this enables:**
1.  **Blocks Plain HTTP OTA**: Only HTTPS firmware downloads are allowed.
2.  **Requires Signed Firmware**: The ESP32 will reject any update that is not cryptographically signed with your RSA-2048 private key.
3.  **SHA256 Integrity Check**: After download, the device computes the SHA256 of the new partition and compares it to the signed hash. A mismatch aborts the update.

---

## 🔐 Security Model

![Security Model](../assets/diagrams/ota-security-workflow.png)

```mermaid
graph TD
    subgraph "Developer / Build Server"
        Bin["firmware.bin"]
        Key[("Private Key (.pem)")]
        Sign["Signing Script"]
        Bin -- "Compute" --> Hash["SHA256 Hash"]
        Hash & Key -- "RSA Sign" --> Signature["Signature (Base64)"]
    end

    subgraph "Cloud / Deployment"
        IoT["HydroponicOne Dashboard"]
        IoT -- "Send via MQTT" --> Payload["{ url, hash, signature }"]
    end

    subgraph "Edge Device (ESP32)"
        Pub[("Public Key (LittleFS)")]
        ESP["OTA Manager"]
        
        Payload -- "1. Verify Sig" --> ESP
        Pub -- "RSA Verify" --> ESP
        
        ESP -- "2. Download" --> HTTPS["HTTPS Firmware"]
        HTTPS -- "3. Validate" --> ESP
        ESP -- "Compute local SHA256" --> Match{"Match?"}
        Match -- "YES" --> Flash["Update Partition & Reboot"]
        Match -- "NO" --> Abort["Abort & Rollback"]
    end
```

**Why this works:** An attacker cannot forge a valid signature without your private key. Even if they intercept the MQTT payload, they cannot substitute a malicious binary because the SHA256 won't match.

---

## 🔑 Managing RSA Keys

HydroponicOne uses RSA-2048 signing. You must generate a public/private key pair.

### Automated Key Generation
Run the following script from the project root:
```bash
python firmware/scripts/generate_keys.py
```

**Results:**
- `firmware/data/ota_priv.pem`: **PRIVATE KEY**. Keep this secret. Never commit it to git.
- `firmware/data/ota_pub.pem`: **PUBLIC KEY**. This is flashed to the ESP32 via LittleFS to verify updates.
- `firmware/data/ota_ca.pem`: **CA CERTIFICATE**. This self-signed X.509 certificate is used to secure your local HTTPS OTA server.
- `firmware/scripts/ota_ca_key.pem`: **CA PRIVATE KEY**. Used by `host_ota.py` to encrypt traffic. Keep this secret.

> [!CAUTION]
> If you lose your `ota_priv.pem`, you will no longer be able to OTA update your devices. You must re-flash them via USB with a new public key.

---

## 🔄 The Secure Update Workflow

### 1. Build your Firmware
Compile your project using PlatformIO:
```bash
cd firmware
pio run -e dht_bmp
```
The binary will be at `.pio/build/dht_bmp/firmware.bin`.

### 2. Sign the Binary
Use the signing script to generate SHA256 + signature:
```bash
python scripts/sign_firmware.py --bin .pio/build/dht_bmp/firmware.bin
```

Output:
```
[*] Firmware: .pio/build/dht_bmp/firmware.bin
[*] Size:     1234567 bytes
[*] SHA256:   a1b2c3d4e5f6...

============================================================
 SIGNED OTA CREDENTIALS — Paste into HydroponicOne Dashboard
============================================================

  SHA256:    a1b2c3d4e5f6...
  Signature: SGVsbG8gV29ybGQ=...

============================================================
```

### 3. Host the Binary
Upload `firmware.bin` to any HTTPS-accessible URL (GitHub Releases, S3 bucket, your own server, etc.).

**Alternatively, host locally via `host_ota.py`:**
If you want to deploy from your local computer inside your local network, you can start a simple HTTPS server that uses the CA cert configured above:
```bash
python scripts/host_ota.py
```
This serves files from `.pio/build/dht_bmp/` over HTTPS on port 8443. The URL you will use in the dashboard is:
`https://<YOUR_LOCAL_IP>:8443/firmware.bin`

### 4. Deploy via Dashboard
1. Navigate to the **OTA Firmware Update** page in the HydroponicOne dashboard.
2. Enter the firmware URL and a version string (for your own reference).
3. Click the **🛡 Shield** toggle to enable **Secure Mode**.
4. Paste the SHA256 hash and Base64 signature from the script output.
5. Click **Deploy Signed Firmware**.

The backend dispatches the payload via MQTT. The ESP32 will:
1. Verify the RSA signature of the SHA256 hash.
2. Download the binary over HTTPS.
3. Compute the SHA256 of the downloaded partition.
4. Compare it against the signed hash.
5. If everything matches, reboot into the new firmware.

---

## 💡 Troubleshooting OTA

- **"Signature Verification Failed"**: Ensure the `ota_pub.pem` on your ESP32 matches the `ota_priv.pem` used to sign the binary. You must re-flash via USB after changing keys.
- **"SHA256 Mismatch"**: The file may have been corrupted during download, or you signed a different binary than the one hosted at the URL.
- **"HTTPS Required"**: You have `ENFORCE_STRICT_SECURITY` enabled but provided an `http://` URL. Use `https://`.
- **Python Dependencies**: Ensure you have installed the requirements:
  ```bash
  pip install -r firmware/scripts/requirements.txt
  ```
