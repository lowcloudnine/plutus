"""SQLite persistence for the Plutus desktop app."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


VALID_METALS = ("Gold", "Silver")


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


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_schema()

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
