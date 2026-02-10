#!/usr/bin/env python3
"""Generate RS256 key pair for custom auth JWT. Paste private key into .env as JWT_PRIVATE_KEY and public key as JWT_PUBLIC_KEY (and NEXT_PUBLIC_JWT_PUBLIC_KEY in frontend .env.local). Use \\n for newlines in .env if needed."""
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def main():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    print("JWT_PRIVATE_KEY (backend .env):")
    print(private_pem)
    print("JWT_PUBLIC_KEY (backend .env and frontend .env.local as NEXT_PUBLIC_JWT_PUBLIC_KEY):")
    print(public_pem)


if __name__ == "__main__":
    main()
