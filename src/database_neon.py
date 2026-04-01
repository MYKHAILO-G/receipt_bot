"""
Neon.tech (serverless PostgreSQL) backend.

Install dependency:
    pip install psycopg2-binary

Usage:
    db = NeonDatabase("postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/dbname?sslmode=require")
"""

import uuid

import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection as PgConnection

from database import Database


class NeonDatabase(Database):
    def __init__(self, connection_string: str):
        """
        Args:
            connection_string: Full Neon connection string from your project dashboard.
                               Format: postgresql://user:pass@ep-xxx.<region>.aws.neon.tech/dbname?sslmode=require
        """
        self._dsn = connection_string
        self._init_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _conn(self) -> PgConnection:
        return psycopg2.connect(self._dsn)

    def _init_db(self):
        with self._conn() as con:
            with con.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        data    JSONB NOT NULL DEFAULT '{}'
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS receipts (
                        uuid    TEXT        NOT NULL,
                        date    TEXT,
                        store   TEXT,
                        item    TEXT,
                        price   NUMERIC,
                        user_id TEXT        NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                    )
                """)

    # ------------------------------------------------------------------
    # User metadata
    # ------------------------------------------------------------------

    def save_user(self, user_id: int | str, user_data: dict) -> None:
        with self._conn() as con:
            with con.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (user_id, data) VALUES (%s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET data = EXCLUDED.data
                    """,
                    (str(user_id), psycopg2.extras.Json(user_data)),
                )

    def get_user(self, user_id: int | str) -> dict | None:
        with self._conn() as con:
            with con.cursor() as cur:
                cur.execute(
                    "SELECT data FROM users WHERE user_id = %s", (str(user_id),)
                )
                row = cur.fetchone()
        return row[0] if row else None  # psycopg2 auto-deserializes JSONB

    # ------------------------------------------------------------------
    # Receipt data
    # ------------------------------------------------------------------

    def save_receipt(self, user_id: int | str, receipt: dict) -> None:
        # Ensure user row exists so the FK constraint doesn't fire
        with self._conn() as con:
            with con.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING",
                    (str(user_id),),
                )
                receipt_uuid = str(uuid.uuid4())
                rows = [
                    (
                        receipt_uuid,
                        receipt.get("date", ""),
                        receipt.get("store", ""),
                        item["name"],
                        item["price"],
                        str(user_id),
                    )
                    for item in receipt["items"]
                ]
                psycopg2.extras.execute_values(
                    cur,
                    "INSERT INTO receipts (uuid, date, store, item, price, user_id) VALUES %s",
                    rows,
                )

    def get_receipts(self, user_id: int | str) -> list[dict] | None:
        with self._conn() as con:
            with con.cursor() as cur:
                # Check user exists first
                cur.execute(
                    "SELECT 1 FROM users WHERE user_id = %s", (str(user_id),)
                )
                if cur.fetchone() is None:
                    return None

                cur.execute(
                    """
                    SELECT uuid, date, store, item, price
                    FROM receipts
                    WHERE user_id = %s
                    ORDER BY date
                    """,
                    (str(user_id),),
                )
                rows = cur.fetchall()

        keys = ["UUID", "Date", "Store", "Item", "Price"]
        return [dict(zip(keys, row)) for row in rows]

    def get_xlsx_path(self, user_id: int | str) -> str | None:
        """Generate a temporary .xlsx file from Postgres data on demand."""
        import os
        import tempfile
        from openpyxl import Workbook

        rows = self.get_receipts(user_id)
        if not rows:
            return None

        wb = Workbook()
        ws = wb.active
        ws.append(["UUID", "Date", "Store", "Item", "Price"])
        for row in rows:
            ws.append([row["UUID"], row["Date"], row["Store"], row["Item"], row["Price"]])

        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        wb.save(tmp.name)
        return os.path.abspath(tmp.name)