"""Create a local HTTPS certificate for VEYTAC's LAN IP (development only).

The CA key is used in memory and discarded. Its public certificate must be
installed and explicitly trusted on each phone/tablet before camera access.
"""

from __future__ import annotations

import argparse
import ipaddress
import socket
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def lan_ip() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(("192.0.2.1", 80))  # route selection only; no packet sent
        return sock.getsockname()[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ip", default=None, help="PC's WiFi IPv4 address")
    parser.add_argument("--out", type=Path,
                        default=Path(__file__).resolve().parents[1] / "apps/web/.certs")
    parser.add_argument("--renew", action="store_true",
                        help="replace an existing certificate (phones must trust the new CA)")
    args = parser.parse_args()
    address = ipaddress.IPv4Address(args.ip or lan_ip())
    out: Path = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    ca_path = out / "lan-ca.crt"
    cert_path = out / "lan-server.crt"
    key_path = out / "lan-server.key"
    if any(p.exists() for p in (ca_path, cert_path, key_path)) and not args.renew:
        raise SystemExit(f"Certificate already exists in {out}. Use --renew to replace it.")

    now = datetime.now(timezone.utc)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "VEYTAC local development CA")])
    ca = (x509.CertificateBuilder()
          .subject_name(ca_name).issuer_name(ca_name)
          .public_key(ca_key.public_key())
          .serial_number(x509.random_serial_number())
          .not_valid_before(now - timedelta(minutes=5))
          .not_valid_after(now + timedelta(days=365))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False,
                                      key_encipherment=False, data_encipherment=False,
                                      key_agreement=False, key_cert_sign=True,
                                      crl_sign=True, encipher_only=False,
                                      decipher_only=False), critical=True)
          .sign(ca_key, hashes.SHA256()))
    server_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    server_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, str(address))])
    server = (x509.CertificateBuilder()
              .subject_name(server_name).issuer_name(ca_name)
              .public_key(server_key.public_key())
              .serial_number(x509.random_serial_number())
              .not_valid_before(now - timedelta(minutes=5))
              .not_valid_after(now + timedelta(days=90))
              .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
              .add_extension(x509.SubjectAlternativeName([
                  x509.IPAddress(address),
                  x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                  x509.DNSName("localhost"),
              ]), critical=False)
              .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
              .sign(ca_key, hashes.SHA256()))
    ca_path.write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    cert_path.write_bytes(server.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(server_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()))
    print(f"LAN URL: https://{address}:5173")
    print(f"Trust this public CA certificate on each phone/tablet: {ca_path}")
    print(f"Private server key stays local and ignored by Git: {key_path}")


if __name__ == "__main__":
    main()
