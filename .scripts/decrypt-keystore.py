#!/usr/bin/env python3
"""Decrypt the encrypted TWA keystore blob and write it to a real .jks file
+ export passwords as $GITHUB_ENV vars. Used by the build-android-twa
workflow when production-blob signing mode is selected.

Reads:
  app/data/twa_credentials.enc   the Fernet-encrypted JSON blob
  $ADMIN_TOKEN_RUNTIME            the encryption key (PBKDF2 input)

Writes:
  $1 (first arg)                  decoded keystore .jks file
  $GITHUB_ENV                     KEYSTORE_PASS, KEY_PASS, KEY_ALIAS
"""
import base64, hashlib, json, os, sys
from cryptography.fernet import Fernet


def main(out_keystore_path: str) -> None:
    token = os.environ.get("ADMIN_TOKEN_RUNTIME") or os.environ.get("ADMIN_TOKEN", "lumora-admin-test")
    salt = b"servia.twa.creds.v1"
    key_bytes = hashlib.pbkdf2_hmac("sha256", token.encode(), salt, 100_000, dklen=32)
    fernet_key = base64.urlsafe_b64encode(key_bytes)

    enc_path = os.path.join(os.environ.get("GITHUB_WORKSPACE", "."), "app/data/twa_credentials.enc")
    encrypted = open(enc_path, "rb").read()
    data = json.loads(Fernet(fernet_key).decrypt(encrypted))

    open(out_keystore_path, "wb").write(base64.b64decode(data["keystore_base64"]))
    print(f"Decrypted keystore → {out_keystore_path} ({os.path.getsize(out_keystore_path)} bytes)")
    print(f"  alias:           {data['key_alias']}")
    print(f"  SHA-256:         {data.get('sha256_fingerprint', '(unknown)')}")

    # Export passwords as workflow env vars (masked from the log)
    github_env = os.environ.get("GITHUB_ENV")
    if github_env:
        with open(github_env, "a") as fp:
            fp.write(f"KEYSTORE_PASS={data['keystore_password']}\n")
            fp.write(f"KEY_PASS={data['key_password']}\n")
            fp.write(f"KEY_ALIAS={data['key_alias']}\n")
        print(f"::add-mask::{data['keystore_password']}")
        if data['key_password'] != data['keystore_password']:
            print(f"::add-mask::{data['key_password']}")
        print("Exported passwords to $GITHUB_ENV")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: decrypt-keystore.py <out.jks>\n")
        sys.exit(2)
    main(sys.argv[1])
