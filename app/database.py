from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parents[1] / "petmate.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def init_db() -> None:
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS child (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                guardian_name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS guardian_settings (
                child_id INTEGER PRIMARY KEY,
                outdoor_enabled INTEGER NOT NULL DEFAULT 1,
                animal_clues_enabled INTEGER NOT NULL DEFAULT 1,
                daily_distance_goal INTEGER NOT NULL DEFAULT 500,
                max_daily_distance INTEGER NOT NULL DEFAULT 3000,
                FOREIGN KEY(child_id) REFERENCES child(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS pet (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_id INTEGER NOT NULL UNIQUE,
                name TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                xp INTEGER NOT NULL DEFAULT 0,
                hunger INTEGER NOT NULL DEFAULT 60,
                mood INTEGER NOT NULL DEFAULT 60,
                bond INTEGER NOT NULL DEFAULT 20,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(child_id) REFERENCES child(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS adventure_day (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_id INTEGER NOT NULL,
                day TEXT NOT NULL,
                distance_meters INTEGER NOT NULL DEFAULT 0,
                exploration_energy INTEGER NOT NULL DEFAULT 0,
                plant_chances INTEGER NOT NULL DEFAULT 0,
                animal_chances INTEGER NOT NULL DEFAULT 0,
                xp INTEGER NOT NULL DEFAULT 0,
                chapter TEXT NOT NULL DEFAULT '小小观察员',
                stage INTEGER NOT NULL DEFAULT 1,
                completed INTEGER NOT NULL DEFAULT 0,
                reward_claimed INTEGER NOT NULL DEFAULT 0,
                UNIQUE(child_id, day),
                FOREIGN KEY(child_id) REFERENCES child(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS inventory_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_id INTEGER NOT NULL,
                item_key TEXT NOT NULL,
                item_name TEXT NOT NULL,
                item_type TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                UNIQUE(child_id, item_key),
                FOREIGN KEY(child_id) REFERENCES child(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS encyclopedia_entry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_id INTEGER NOT NULL,
                entry_type TEXT NOT NULL,
                entry_key TEXT NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                knowledge TEXT NOT NULL,
                safety_tip TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 1,
                friendship INTEGER NOT NULL DEFAULT 0,
                adopted INTEGER NOT NULL DEFAULT 0,
                first_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(child_id, entry_type, entry_key),
                FOREIGN KEY(child_id) REFERENCES child(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS scan_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_id INTEGER NOT NULL,
                plant_key TEXT NOT NULL,
                plant_name TEXT NOT NULL,
                food_key TEXT NOT NULL,
                food_name TEXT NOT NULL,
                xp INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(child_id) REFERENCES child(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS animal_clue_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_id INTEGER NOT NULL,
                animal_key TEXT NOT NULL,
                animal_name TEXT NOT NULL,
                friendship_added INTEGER NOT NULL,
                xp INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(child_id) REFERENCES child(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS feed_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_id INTEGER NOT NULL,
                pet_id INTEGER NOT NULL,
                food_key TEXT NOT NULL,
                food_name TEXT NOT NULL,
                xp INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(child_id) REFERENCES child(id) ON DELETE CASCADE,
                FOREIGN KEY(pet_id) REFERENCES pet(id) ON DELETE CASCADE
            );
            """
        )

