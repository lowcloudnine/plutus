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
class Contact:
    id: int | None
    name: str
    address_line1: str
    address_line2: str
    city: str
    state: str
    postal_code: str
    country: str
    phone: str
    url: str
    is_buyer: bool
    is_seller: bool

    @property
    def role_label(self) -> str:
        if self.is_buyer and self.is_seller:
            return "Buyer and seller"
        if self.is_buyer:
            return "Buyer"
        if self.is_seller:
            return "Seller"
        return "Contact"


@dataclass(slots=True)
class Holding:
    id: int | None
    metal: str
    quantity: float
    unit_cost: float
    contact_id: int | None
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
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address_line1 TEXT NOT NULL DEFAULT '',
                address_line2 TEXT NOT NULL DEFAULT '',
                city TEXT NOT NULL DEFAULT '',
                state TEXT NOT NULL DEFAULT '',
                postal_code TEXT NOT NULL DEFAULT '',
                country TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                is_buyer INTEGER NOT NULL DEFAULT 0 CHECK (is_buyer IN (0, 1)),
                is_seller INTEGER NOT NULL DEFAULT 1 CHECK (is_seller IN (0, 1)),
                CHECK (is_buyer = 1 OR is_seller = 1)
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metal TEXT NOT NULL CHECK (metal IN ('Gold', 'Silver')),
                quantity REAL NOT NULL CHECK (quantity > 0),
                unit_cost REAL NOT NULL CHECK (unit_cost >= 0),
                contact_id INTEGER REFERENCES contacts(id) ON DELETE SET NULL,
                purchased_on TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT ''
            )
            """
        )
        self._migrate_vendor_text_to_contacts()
        self.connection.commit()

    def _table_columns(self, table_name: str) -> set[str]:
        rows = self.connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {str(row["name"]) for row in rows}

    def _migrate_vendor_text_to_contacts(self) -> None:
        holding_columns = self._table_columns("holdings")
        if "contact_id" not in holding_columns:
            self.connection.execute(
                "ALTER TABLE holdings ADD COLUMN contact_id INTEGER REFERENCES contacts(id) ON DELETE SET NULL"
            )
            holding_columns.add("contact_id")

        if "vendor" not in holding_columns:
            return

        rows = self.connection.execute(
            """
            SELECT DISTINCT trim(vendor) AS vendor_name
            FROM holdings
            WHERE contact_id IS NULL AND trim(vendor) != ''
            ORDER BY vendor_name
            """
        ).fetchall()
        for row in rows:
            vendor_name = str(row["vendor_name"])
            contact_id = self._contact_id_for_name(vendor_name)
            if contact_id is None:
                contact_id = self.add_contact(
                    Contact(
                        id=None,
                        name=vendor_name,
                        address_line1="",
                        address_line2="",
                        city="",
                        state="",
                        postal_code="",
                        country="",
                        phone="",
                        url="",
                        is_buyer=False,
                        is_seller=True,
                    ),
                    commit=False,
                )
            self.connection.execute(
                "UPDATE holdings SET contact_id = ? WHERE contact_id IS NULL AND trim(vendor) = ?",
                (contact_id, vendor_name),
            )

    def _contact_id_for_name(self, name: str) -> int | None:
        row = self.connection.execute(
            "SELECT id FROM contacts WHERE lower(name) = lower(?) ORDER BY id LIMIT 1",
            (name,),
        ).fetchone()
        return None if row is None else int(row["id"])

    def list_contacts(self, sellers_only: bool = False) -> list[Contact]:
        where_clause = "WHERE is_seller = 1" if sellers_only else ""
        rows = self.connection.execute(
            f"""
            SELECT id, name, address_line1, address_line2, city, state, postal_code,
                   country, phone, url, is_buyer, is_seller
            FROM contacts
            {where_clause}
            ORDER BY name COLLATE NOCASE ASC, id ASC
            """
        ).fetchall()
        return [
            Contact(
                id=int(row["id"]),
                name=str(row["name"]),
                address_line1=str(row["address_line1"]),
                address_line2=str(row["address_line2"]),
                city=str(row["city"]),
                state=str(row["state"]),
                postal_code=str(row["postal_code"]),
                country=str(row["country"]),
                phone=str(row["phone"]),
                url=str(row["url"]),
                is_buyer=bool(row["is_buyer"]),
                is_seller=bool(row["is_seller"]),
            )
            for row in rows
        ]

    def add_contact(self, contact: Contact, commit: bool = True) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO contacts (
                name, address_line1, address_line2, city, state, postal_code,
                country, phone, url, is_buyer, is_seller
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                contact.name,
                contact.address_line1,
                contact.address_line2,
                contact.city,
                contact.state,
                contact.postal_code,
                contact.country,
                contact.phone,
                contact.url,
                int(contact.is_buyer),
                int(contact.is_seller),
            ),
        )
        if commit:
            self.connection.commit()
        return int(cursor.lastrowid)

    def list_holdings(self) -> list[Holding]:
        rows = self.connection.execute(
            """
            SELECT h.id, h.metal, h.quantity, h.unit_cost, h.contact_id,
                   coalesce(c.name, '') AS vendor, h.purchased_on, h.notes
            FROM holdings AS h
            LEFT JOIN contacts AS c ON c.id = h.contact_id
            ORDER BY h.metal ASC, h.purchased_on DESC, h.id DESC
            """
        ).fetchall()
        return [Holding(**dict(row)) for row in rows]

    def add_holding(self, holding: Holding) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO holdings (metal, quantity, unit_cost, contact_id, purchased_on, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                holding.metal,
                holding.quantity,
                holding.unit_cost,
                holding.contact_id,
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
            SET metal = ?, quantity = ?, unit_cost = ?, contact_id = ?, purchased_on = ?, notes = ?
            WHERE id = ?
            """,
            (
                holding.metal,
                holding.quantity,
                holding.unit_cost,
                holding.contact_id,
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
