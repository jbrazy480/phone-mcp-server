"""Masked audit records and persistent rolling-hour reservations."""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from .guards import GuardError


def mask(number: str) -> str:
    return "***" + number[-4:] if number else "unknown"


class Audit:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: str, outcome: str, now: datetime, to: str = "", kind: str = "") -> None:
        # Do not store messages, codes, credentials, provider errors, or arbitrary input.
        record = {"time": now.isoformat(), "event": event, "outcome": outcome,
                  "to": mask(to), "kind": kind}
        fd = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        with os.fdopen(fd, "a") as stream:
            stream.write(json.dumps(record) + "\n")
            stream.flush()
            os.fsync(stream.fileno())


class RateLimit:
    def __init__(self, path: Path, maximum: int):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path, self.maximum = path, maximum
        with sqlite3.connect(path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS attempts (at REAL NOT NULL)")

    def check(self, now: datetime, reserve: bool = False) -> None:
        with sqlite3.connect(self.path, timeout=10) as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("DELETE FROM attempts WHERE at <= ?", (now.timestamp() - 3600,))
            count = conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
            if count >= self.maximum:
                raise GuardError("Per-hour outbound rate limit reached")
            if reserve:
                conn.execute("INSERT INTO attempts VALUES (?)", (now.timestamp(),))
