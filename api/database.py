"""Database connection adapter: SQLite for local work, Neon PostgreSQL for deployed APIs.

Set DATABASE_URL to a Neon Postgres connection string. Never commit credentials.
The adapter keeps existing repository operations compatible while migrations are incremental.
"""
from __future__ import annotations
import os
import sqlite3


def postgres_enabled() -> bool:
    return bool(os.getenv("DATABASE_URL", "").strip())


class PostgresConnection:
    def __init__(self, url: str):
        import psycopg
        self.connection = psycopg.connect(url, connect_timeout=10)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                self.connection.rollback()
            else:
                self.connection.commit()
        finally:
            self.connection.close()

    def execute(self, sql: str, values=()):
        if sql.strip().upper() == "BEGIN IMMEDIATE":
            return None  # Psycopg starts a transaction implicitly.
        converted = sql.replace("?", "%s")
        return self.connection.execute(converted, values)

    def executescript(self, script: str):
        for statement in script.split(";"):
            statement = statement.strip()
            if statement and not statement.upper().startswith("PRAGMA "):
                self.execute(statement)


def connect(path: str, *, foreign_keys: bool = False):
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return PostgresConnection(url)
    db = sqlite3.connect(path, timeout=15)
    if foreign_keys:
        db.execute("PRAGMA foreign_keys=ON")
    return db
