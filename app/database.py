from __future__ import annotations

import sqlite3
import os
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_LOCAL_DB_PATH = Path(__file__).resolve().parents[1] / "petmate.db"


def resolve_db_path() -> Path:
    configured = os.getenv("PETMATE_DB_PATH")
    if configured:
        return Path(configured)
    if os.getenv("STREAMLIT_SERVER_PORT") or os.getenv("STREAMLIT_SHARING"):
        return Path(tempfile.gettempdir()) / "petmate.db"
    return DEFAULT_LOCAL_DB_PATH


DB_PATH = resolve_db_path()


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
                friends_enabled INTEGER NOT NULL DEFAULT 0,
                garden_help_enabled INTEGER NOT NULL DEFAULT 1,
                garden_likes_enabled INTEGER NOT NULL DEFAULT 1,
                daily_distance_goal INTEGER NOT NULL DEFAULT 500,
                max_daily_distance INTEGER NOT NULL DEFAULT 3000,
                sleep_start TEXT NOT NULL DEFAULT '21:00',
                sleep_end TEXT NOT NULL DEFAULT '07:00',
                study_mode_enabled INTEGER NOT NULL DEFAULT 1,
                study_start TEXT NOT NULL DEFAULT '08:00',
                study_end TEXT NOT NULL DEFAULT '17:00',
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
                steps INTEGER NOT NULL DEFAULT 0,
                active_minutes INTEGER NOT NULL DEFAULT 0,
                estimated_kcal REAL NOT NULL DEFAULT 0,
                activity_energy INTEGER NOT NULL DEFAULT 0,
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
                mood INTEGER NOT NULL DEFAULT 50,
                trust INTEGER NOT NULL DEFAULT 20,
                curiosity INTEGER NOT NULL DEFAULT 40,
                home_level INTEGER NOT NULL DEFAULT 1,
                growth_points INTEGER NOT NULL DEFAULT 0,
                away_state TEXT NOT NULL DEFAULT 'home',
                away_reason TEXT NOT NULL DEFAULT '',
                keepsake TEXT NOT NULL DEFAULT '',
                away_at TEXT,
                memory TEXT NOT NULL DEFAULT '',
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

            CREATE TABLE IF NOT EXISTS animal_interaction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_id INTEGER NOT NULL,
                animal_key TEXT NOT NULL,
                animal_name TEXT NOT NULL,
                action TEXT NOT NULL,
                friendship_added INTEGER NOT NULL,
                energy_cost INTEGER NOT NULL DEFAULT 0,
                xp INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(child_id) REFERENCES child(id) ON DELETE CASCADE
            );
            """
        )
        ensure_column(db, "adventure_day", "steps", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(db, "adventure_day", "active_minutes", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(db, "adventure_day", "estimated_kcal", "REAL NOT NULL DEFAULT 0")
        ensure_column(db, "adventure_day", "activity_energy", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(db, "guardian_settings", "sleep_start", "TEXT NOT NULL DEFAULT '21:00'")
        ensure_column(db, "guardian_settings", "sleep_end", "TEXT NOT NULL DEFAULT '07:00'")
        ensure_column(db, "guardian_settings", "study_mode_enabled", "INTEGER NOT NULL DEFAULT 1")
        ensure_column(db, "guardian_settings", "study_start", "TEXT NOT NULL DEFAULT '08:00'")
        ensure_column(db, "guardian_settings", "study_end", "TEXT NOT NULL DEFAULT '17:00'")
        ensure_column(db, "guardian_settings", "friends_enabled", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(db, "guardian_settings", "garden_help_enabled", "INTEGER NOT NULL DEFAULT 1")
        ensure_column(db, "guardian_settings", "garden_likes_enabled", "INTEGER NOT NULL DEFAULT 1")
        ensure_column(db, "encyclopedia_entry", "mood", "INTEGER NOT NULL DEFAULT 50")
        ensure_column(db, "encyclopedia_entry", "trust", "INTEGER NOT NULL DEFAULT 20")
        ensure_column(db, "encyclopedia_entry", "curiosity", "INTEGER NOT NULL DEFAULT 40")
        ensure_column(db, "encyclopedia_entry", "home_level", "INTEGER NOT NULL DEFAULT 1")
        ensure_column(db, "encyclopedia_entry", "growth_points", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(db, "encyclopedia_entry", "away_state", "TEXT NOT NULL DEFAULT 'home'")
        ensure_column(db, "encyclopedia_entry", "away_reason", "TEXT NOT NULL DEFAULT ''")
        ensure_column(db, "encyclopedia_entry", "keepsake", "TEXT NOT NULL DEFAULT ''")
        ensure_column(db, "encyclopedia_entry", "away_at", "TEXT")
        ensure_column(db, "encyclopedia_entry", "memory", "TEXT NOT NULL DEFAULT ''")
        ensure_column(db, "animal_interaction_log", "energy_cost", "INTEGER NOT NULL DEFAULT 0")


def ensure_column(db: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
