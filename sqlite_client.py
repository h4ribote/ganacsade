import sqlite3
from typing import Optional, List, Tuple, Dict

class SQLiteClient:
    def __init__(self, db_path: str = "ganacsade.db"):
        self.db_path = db_path

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Initializes the database tables."""
        with self._get_conn() as conn:
            cursor = conn.cursor()

            # Items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    item_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)

            # Watch list table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS watch_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    threshold_price INTEGER NOT NULL
                )
            """)

            # Bot config table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bot_config (
                    conf_name TEXT PRIMARY KEY,
                    conf_value TEXT
                )
            """)
            conn.commit()

    def get_item_id(self, name: str) -> Optional[int]:
        """Gets item ID by name (case-insensitive)."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_id FROM items WHERE name = ? COLLATE NOCASE", (name,))
            row = cursor.fetchone()
            return row[0] if row else None

    def get_item_name(self, item_id: int) -> Optional[str]:
        """Gets item name by ID."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM items WHERE item_id = ?", (item_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    def upsert_item(self, item_id: int, name: str):
        """Inserts or updates an item."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO items (item_id, name) VALUES (?, ?)", (item_id, name))
            conn.commit()

    def upsert_items(self, items: Dict[int, str]):
        """Bulk upsert items."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.executemany("INSERT OR REPLACE INTO items (item_id, name) VALUES (?, ?)",
                               [(k, v) for k, v in items.items()])
            conn.commit()

    def add_watch(self, user_id: int, item_id: int, threshold_price: int) -> int:
        """Adds a watch entry."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO watch_list (user_id, item_id, threshold_price)
                VALUES (?, ?, ?)
            """, (user_id, item_id, threshold_price))
            conn.commit()
            return cursor.lastrowid

    def remove_watch(self, watch_id: int):
        """Removes a watch entry."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM watch_list WHERE id = ?", (watch_id,))
            conn.commit()

    def get_all_watches(self) -> List[Tuple[int, int, int, int]]:
        """Returns all watches: (id, user_id, item_id, threshold_price)."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, user_id, item_id, threshold_price FROM watch_list")
            return cursor.fetchall()

    def set_config(self, key: str, value: str):
        """Sets a config value."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO bot_config (conf_name, conf_value) VALUES (?, ?)", (key, value))
            conn.commit()

    def get_config(self, key: str) -> Optional[str]:
        """Gets a config value."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT conf_value FROM bot_config WHERE conf_name = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else None
