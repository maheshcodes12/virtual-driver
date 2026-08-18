#!/usr/bin/env python3
"""
LeakTrace CLI
Usage:
  leaktrace activate <key>         - Activate this installation
  leaktrace decrypt <file>         - Decrypt an encrypted PDF
  leaktrace verify  <file>         - Reveal origin of a LeakTrace PDF
  leaktrace genkey  [machine_id]   - (Admin) Generate an activation key
  leaktrace whoami                 - Show activation status
"""

import sys
import os
import pathlib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

from core.crypto import decrypt, load_master_password
from core.watermark import extract
from core.logger import lookup
from core.config import MASTER_KEY_PATH
from keys.activation import activate, check_activated, generate_key, _get_machine_id


def require_activation():
    valid, reason = check_activated()
    if not valid:
        print(f"[!] {reason}")
        sys.exit(1)


def cmd_activate(args):
    if not args:
        print("Usage: leaktrace activate <KEY>")
        sys.exit(1)
    activate(args[0])


def cmd_genkey(args):
    machine_id = args[0] if args else None
    days = int(args[1]) if len(args) > 1 else 365
    key = generate_key(machine_id, days)
    mid = machine_id or _get_machine_id()
    print(f"Machine ID : {mid}")
    print(f"Valid days : {days}")
    print(f"Key        : {key}")


def cmd_whoami(_):
    valid, reason = check_activated()
    machine_id = _get_machine_id()
    status = "✓ Activated" if valid else "✗ Not activated"
    print(f"Machine ID : {machine_id}")
    print(f"Status     : {status}")
    print(f"Details    : {reason}")


def cmd_decrypt(args):
    require_activation()
    if not args:
        print("Usage: leaktrace decrypt <file>")
        sys.exit(1)

    path = args[0]
    if not os.path.exists(path):
        print(f"[!] File not found: {path}")
        sys.exit(1)

    password = load_master_password(MASTER_KEY_PATH)
    with open(path, "rb") as f:
        data = f.read()

    try:
        decrypted = decrypt(data, password)
    except ValueError as e:
        print(f"[!] {e}")
        sys.exit(1)

    p = pathlib.Path(path)
    stem = p.stem if p.suffix != ".pdf" else p.with_suffix("").stem
    out_path = str(p.parent / (stem + "_decrypted.pdf"))
    with open(out_path, "wb") as f:
        f.write(decrypted)

    print(f"[✓] Decrypted → {out_path}")


def cmd_verify(args):
    require_activation()
    if not args:
        print("Usage: leaktrace verify <file>")
        sys.exit(1)

    path = args[0]
    if not os.path.exists(path):
        print(f"[!] File not found: {path}")
        sys.exit(1)

    with open(path, "rb") as f:
        data = f.read()

    password = load_master_password(MASTER_KEY_PATH)
    try:
        pdf_bytes = decrypt(data, password)
        print("[i] File is encrypted — decrypted for analysis.")
    except Exception:
        pdf_bytes = data
        print("[i] File is not encrypted — analyzing as-is.")

    doc_id = extract(pdf_bytes)
    if not doc_id:
        print("[!] No LeakTrace watermark found in this file.")
        sys.exit(1)

    print(f"\n{'='*40}")
    print(f"  LEAKTRACE VERIFICATION REPORT")
    print(f"{'='*40}")
    print(f"  Watermark ID : {doc_id}")

    record = lookup(doc_id)
    if record:
        print(f"  User         : {record['user']}")
        print(f"  Hostname     : {record['hostname']}")
        print(f"  Timestamp    : {record['timestamp']} UTC")
        print(f"  Document     : {record['title']}")
        print(f"  File Hash    : {record['file_hash'][:16]}...")
        print(f"  Saved At     : {record['output_path']}")
    else:
        print("  [!] Watermark found but no matching log entry.")
        print("      (File may be from another LeakTrace instance)")

    print(f"{'='*40}\n")


COMMANDS = {
    "activate": cmd_activate,
    "decrypt":  cmd_decrypt,
    "verify":   cmd_verify,
    "genkey":   cmd_genkey,
    "whoami":   cmd_whoami,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(0)
    COMMANDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
