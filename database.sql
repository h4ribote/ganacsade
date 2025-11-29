CREATE TABLE IF NOT EXISTS items (
    item_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS watch_list (
    item_id INTEGER PRIMARY KEY,
    threshold_price INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS bot_config (
    conf_name TEXT PRIMARY KEY,
    conf_value TEXT
);
