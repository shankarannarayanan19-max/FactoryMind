"""Local SQLite persistence layer for FactoryMind."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


class FactoryDatabase:
    def __init__(self, db_path: str = "data/factorymind.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_tables(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS world_state (
                    state_key TEXT PRIMARY KEY,
                    state_value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    turn INTEGER NOT NULL,
                    user_input TEXT,
                    llm_command TEXT,
                    observation TEXT,
                    room_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS assets (
                    asset_id TEXT PRIMARY KEY,
                    asset_name TEXT,
                    room_id TEXT,
                    status TEXT,
                    health_state TEXT,
                    metadata TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS inventory (
                    item_id TEXT PRIMARY KEY,
                    item_name TEXT,
                    rack TEXT,
                    quantity INTEGER DEFAULT 0,
                    reserved_quantity INTEGER DEFAULT 0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    severity TEXT,
                    message TEXT,
                    room_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def save_world_state(self, key: str, value: Any) -> None:
        encoded_value = json.dumps(value)

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO world_state (state_key, state_value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(state_key)
                DO UPDATE SET
                    state_value = excluded.state_value,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (key, encoded_value),
            )

    def load_world_state(self, key: str, default: Any = None) -> Any:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT state_value FROM world_state WHERE state_key = ?",
                (key,),
            ).fetchone()

        if row is None:
            return default

        return json.loads(row["state_value"])

    def log_action(
        self,
        turn: int,
        user_input: str,
        llm_command: str,
        observation: str,
        room_id: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO actions
                    (turn, user_input, llm_command, observation, room_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (turn, user_input, llm_command, observation, room_id),
            )

    def save_conversation(self, role: str, content: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversations (role, content)
                VALUES (?, ?)
                """,
                (role, content),
            )

    def get_recent_conversation(self, limit: int = 10) -> List[Dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content
                FROM conversations
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {"role": row["role"], "content": row["content"]}
            for row in reversed(rows)
        ]

    def save_inventory_item(
        self,
        item_id: str,
        item_name: str,
        rack: str,
        quantity: int,
        reserved_quantity: int = 0,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO inventory
                    (item_id, item_name, rack, quantity, reserved_quantity)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(item_id)
                DO UPDATE SET
                    item_name = excluded.item_name,
                    rack = excluded.rack,
                    quantity = excluded.quantity,
                    reserved_quantity = excluded.reserved_quantity,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    item_id,
                    item_name,
                    rack,
                    quantity,
                    reserved_quantity,
                ),
            )

    def reserve_inventory(self, item_id: str, amount: int = 1) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT quantity, reserved_quantity
                FROM inventory
                WHERE item_id = ?
                """,
                (item_id,),
            ).fetchone()

            if row is None:
                return False

            available = row["quantity"] - row["reserved_quantity"]

            if available < amount:
                return False

            connection.execute(
                """
                UPDATE inventory
                SET reserved_quantity = reserved_quantity + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE item_id = ?
                """,
                (amount, item_id),
            )

        return True