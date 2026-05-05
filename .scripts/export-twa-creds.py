#!/usr/bin/env python3
"""Read .ci/twa/creds.json and append KEYSTORE_PASS / KEY_PASS / KEY_ALIAS
to $GITHUB_ENV so the gradle build step picks them up. Stdlib only —
no cryptography dep in CI."""
import json, os, sys


def main() -> None:
    creds_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.environ.get("GITHUB_WORKSPACE", "."), ".ci/twa/creds.json")
    c = json.load(open(creds_path))
    ge_path = os.environ.get("GITHUB_ENV")
    if ge_path:
        with open(ge_path, "a") as ge:
            ge.write(f"KEYSTORE_PASS={c['keystore_password']}\n")
            ge.write(f"KEY_PASS={c['key_password']}\n")
            ge.write(f"KEY_ALIAS={c['key_alias']}\n")
    # Mask passwords in the workflow log
    print(f"::add-mask::{c['keystore_password']}")
    if c['key_password'] != c['keystore_password']:
        print(f"::add-mask::{c['key_password']}")
    print(f"alias={c['key_alias']}  sha256={c.get('sha256_fingerprint','?')}")


if __name__ == "__main__":
    main()
