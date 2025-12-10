import pymysql
from typing import Optional, List, Tuple, Dict
import os
from contextlib import closing

class MySQLClient:
    def __init__(self, host: str, port: int, user: str, password: str, db_name: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db_name = db_name

    def _get_conn(self):
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.db_name,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.Cursor
        )

    def init_db(self):
        """Initializes the database tables from database.sql."""
        # For MySQL, we need to create the database if it doesn't exist?
        # Usually client connects to a specific DB.
        # Assuming the DB exists, we just run the schema.
        # If DB doesn't exist, we might fail to connect in _get_conn().
        # However, typically the user should create the DB first or we connect to 'mysql' to create it.
        # Given the config has DB Name, we assume it exists or we can't connect to it yet.

        # Let's try to connect. If DB doesn't exist, we might error.
        # But for now, let's assume the DB 'ganacsade' exists or the user created it.
        # We will just run the table creation scripts.

        sql_file_path = os.path.join(os.path.dirname(__file__), 'database.sql')
        with open(sql_file_path, 'r') as f:
            sql_script = f.read()

        # Split by ';' to execute statements one by one
        statements = [s.strip() for s in sql_script.split(';') if s.strip()]

        with closing(self._get_conn()) as conn:
            with conn.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)
            conn.commit()

    def get_item_id(self, name: str) -> Optional[int]:
        """Gets item ID by name (case-insensitive)."""
        with closing(self._get_conn()) as conn:
            with conn.cursor() as cursor:
                # MySQL is case-insensitive by default for VARCHAR usually
                cursor.execute("SELECT item_id FROM items WHERE name = %s", (name,))
                row = cursor.fetchone()
                return row[0] if row else None

    def get_item_name(self, item_id: int) -> Optional[str]:
        """Gets item name by ID."""
        with closing(self._get_conn()) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT name FROM items WHERE item_id = %s", (item_id,))
                row = cursor.fetchone()
                return row[0] if row else None

    def upsert_item(self, item_id: int, name: str):
        """Inserts or updates an item."""
        with closing(self._get_conn()) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO items (item_id, name) VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE name = VALUES(name)
                """, (item_id, name))
            conn.commit()

    def upsert_items(self, items: Dict[int, str]):
        """Bulk upsert items."""
        if not items:
            return

        values = [(k, v) for k, v in items.items()]
        with closing(self._get_conn()) as conn:
            with conn.cursor() as cursor:
                cursor.executemany("""
                    INSERT INTO items (item_id, name) VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE name = VALUES(name)
                """, values)
            conn.commit()

    def add_watch(self, item_id: int, threshold_price: int):
        """Adds or updates a watch entry."""
        with closing(self._get_conn()) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO watch_list (item_id, threshold_price)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE threshold_price = VALUES(threshold_price)
                """, (item_id, threshold_price))
            conn.commit()

    def remove_watch(self, item_id: int):
        """Removes a watch entry."""
        with closing(self._get_conn()) as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM watch_list WHERE item_id = %s", (item_id,))
            conn.commit()

    def get_all_watches(self) -> List[Tuple[int, int]]:
        """Returns all watches: (item_id, threshold_price)."""
        with closing(self._get_conn()) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT item_id, threshold_price FROM watch_list")
                return list(cursor.fetchall())

    def set_config(self, key: str, value: str):
        """Sets a config value."""
        with closing(self._get_conn()) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO bot_config (conf_name, conf_value) VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE conf_value = VALUES(conf_value)
                """, (key, value))
            conn.commit()

    def get_config(self, key: str) -> Optional[str]:
        """Gets a config value."""
        with closing(self._get_conn()) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT conf_value FROM bot_config WHERE conf_name = %s", (key,))
                row = cursor.fetchone()
                return row[0] if row else None
