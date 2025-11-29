import sqlite3
from typing import Optional, List, Tuple, Dict
import os

class SQLiteClient:
    def __init__(self, db_path: str = "ganacsade.db"):
        self.db_path = db_path

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Initializes the database tables from database.sql."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            sql_file_path = os.path.join(os.path.dirname(__file__), 'database.sql')
            with open(sql_file_path, 'r') as f:
                sql_script = f.read()
            cursor.executescript(sql_script)
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

    def add_watch(self, item_id: int, threshold_price: int):
        """Adds or updates a watch entry."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO watch_list (item_id, threshold_price)
                VALUES (?, ?)
            """, (item_id, threshold_price))
            conn.commit()

    def remove_watch(self, item_id: int):
        """Removes a watch entry."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM watch_list WHERE item_id = ?", (item_id,))
            conn.commit()

    def get_all_watches(self) -> List[Tuple[int, int]]:
        """Returns all watches: (item_id, threshold_price)."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_id, threshold_price FROM watch_list")
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
