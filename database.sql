CREATE TABLE IF NOT EXISTS items (
    item_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS watch_list (
    item_id INTEGER PRIMARY KEY,
    threshold_price INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS bot_config (
    conf_name VARCHAR(255) PRIMARY KEY,
    conf_value TEXT
);
