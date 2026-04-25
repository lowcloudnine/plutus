"""Encrypted SQLite persistence for the Plutus desktop app."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

try:
    from sqlcipher3 import dbapi2 as sqlcipher
except ImportError as exc:  # pragma: no cover - exercised only when dependency is missing.
    sqlcipher = None
    _SQLCIPHER_IMPORT_ERROR = exc
else:
    _SQLCIPHER_IMPORT_ERROR = None


VALID_METALS = ("Gold", "Silver")
SQLITE_HEADER = b"SQLite format 3\x00"


class DatabaseError(RuntimeError):
    """Base error for database setup and access failures."""


class DatabaseDriverError(DatabaseError):
    """Raised when the SQLCipher driver is not available."""


class DatabasePasswordError(DatabaseError):
    """Raised when an encrypted database cannot be opened with the password."""


class PlaintextDatabaseError(DatabaseError):
    """Raised when an existing SQLite database has not been encrypted yet."""


@dataclass(slots=True)
class Holding:
    id: int | None
    metal: str
    quantity: float
    unit_cost: float
    vendor: str
    purchased_on: str
    notes: str

    @property
    def total_cost(self) -> float:
        return self.quantity * self.unit_cost


def is_plaintext_sqlite_database(db_path: Path) -> bool:
    if not db_path.exists() or db_path.stat().st_size == 0:
        return False
    with db_path.open("rb") as database_file:
        return database_file.read(len(SQLITE_HEADER)) == SQLITE_HEADER


def _require_sqlcipher() -> None:
    if sqlcipher is None:
        raise DatabaseDriverError(
            "SQLCipher support is not installed. Run `uv sync` to install project dependencies."
        ) from _SQLCIPHER_IMPORT_ERROR


def _sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def encrypt_plaintext_database(db_path: Path, password: str) -> None:
    """Convert an existing plaintext SQLite database into a SQLCipher database."""
    _require_sqlcipher()
    if not is_plaintext_sqlite_database(db_path):
        return

    temp_file = tempfile.NamedTemporaryFile(
        dir=db_path.parent,
        prefix=f".{db_path.name}.",
        suffix=".encrypted",
        delete=False,
    )
    encrypted_path = Path(temp_file.name)
    temp_file.close()
    encrypted_path.unlink()

    connection = sqlcipher.connect(str(db_path))
    try:
        connection.execute(
            f"ATTACH DATABASE {_sql_quote(str(encrypted_path))} AS encrypted "
            f"KEY {_sql_quote(password)}"
        )
        connection.execute("SELECT sqlcipher_export('encrypted')")
        connection.execute("DETACH DATABASE encrypted")
        connection.commit()
    except Exception as exc:
        raise DatabasePasswordError(f"Could not encrypt the existing database: {exc}") from exc
    finally:
        connection.close()

    try:
        Database(encrypted_path, password).close()
    except DatabaseError:
        encrypted_path.unlink(missing_ok=True)
        raise

    os.replace(encrypted_path, db_path)


class Database:
    def __init__(self, db_path: Path, password: str) -> None:
        _require_sqlcipher()
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        if is_plaintext_sqlite_database(self.db_path):
            raise PlaintextDatabaseError(
                "This database is a normal SQLite file and must be encrypted before use."
            )

        self.connection = sqlcipher.connect(str(self.db_path))
        self.connection.row_factory = sqlcipher.Row
        try:
            self.connection.execute(f"PRAGMA key = {_sql_quote(password)}")
            self.connection.execute("SELECT count(*) FROM sqlite_master").fetchone()
            self._create_schema()
        except Exception as exc:
            self.connection.close()
            raise DatabasePasswordError(
                "Plutus could not unlock that database. Check the password and try again."
            ) from exc

    def _create_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metal TEXT NOT NULL CHECK (metal IN ('Gold', 'Silver')),
                quantity REAL NOT NULL CHECK (quantity > 0),
                unit_cost REAL NOT NULL CHECK (unit_cost >= 0),
                vendor TEXT NOT NULL DEFAULT '',
                purchased_on TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT ''
            )
            """
        )
        self.connection.commit()

    def list_holdings(self) -> list[Holding]:
        rows = self.connection.execute(
            """
            SELECT id, metal, quantity, unit_cost, vendor, purchased_on, notes
            FROM holdings
            ORDER BY metal ASC, purchased_on DESC, id DESC
            """
        ).fetchall()
        return [Holding(**dict(row)) for row in rows]

    def add_holding(self, holding: Holding) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO holdings (metal, quantity, unit_cost, vendor, purchased_on, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                holding.metal,
                holding.quantity,
                holding.unit_cost,
                holding.vendor,
                holding.purchased_on,
                holding.notes,
            ),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def update_holding(self, holding: Holding) -> None:
        if holding.id is None:
            raise ValueError("Holding id is required for updates.")
        self.connection.execute(
            """
            UPDATE holdings
            SET metal = ?, quantity = ?, unit_cost = ?, vendor = ?, purchased_on = ?, notes = ?
            WHERE id = ?
            """,
            (
                holding.metal,
                holding.quantity,
                holding.unit_cost,
                holding.vendor,
                holding.purchased_on,
                holding.notes,
                holding.id,
            ),
        )
        self.connection.commit()

    def delete_holding(self, holding_id: int) -> None:
        self.connection.execute("DELETE FROM holdings WHERE id = ?", (holding_id,))
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
