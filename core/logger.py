import sqlite3
import socket
import hashlib
from datetime import datetime
from .config import DB_PATH


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS print_jobs (
            doc_id      TEXT PRIMARY KEY,
            user        TEXT,
            hostname    TEXT,
            timestamp   TEXT,
            title       TEXT,
            file_hash   TEXT,
            output_path TEXT
        )
    """)
    con.commit()
    con.close()


def log_job(doc_id: str, user: str, title: str, file_path: str):
    init_db()
    file_hash = _sha256(file_path)
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT OR REPLACE INTO print_jobs VALUES (?,?,?,?,?,?,?)",
        (doc_id, user, socket.gethostname(), datetime.utcnow().isoformat(), title, file_hash, file_path)
    )
    con.commit()
    con.close()


def lookup(doc_id: str) -> dict | None:
    init_db()
    con = sqlite3.connect(DB_PATH)
    row = con.execute("SELECT * FROM print_jobs WHERE doc_id=?", (doc_id,)).fetchone()
    con.close()
    if not row:
        return None
    keys = ["doc_id", "user", "hostname", "timestamp", "title", "file_hash", "output_path"]
    return dict(zip(keys, row))


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except Exception:
        return "unknown"
    return h.hexdigest()
