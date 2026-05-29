
CREATE TABLE IF NOT EXISTS urls (
   
    id          INTEGER PRIMARY KEY AUTOINCREMENT,

    short_code  TEXT UNIQUE NOT NULL,

    original_url TEXT NOT NULL,

    created_at  TEXT DEFAULT CURRENT_TIMESTAMP,

    expires_at  TEXT
);

CREATE TABLE IF NOT EXISTS clicks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,

    url_id      INTEGER NOT NULL,

    clicked_at  TEXT DEFAULT CURRENT_TIMESTAMP,

    ip_address  TEXT,
    country     TEXT,
    device      TEXT,  
    referrer    TEXT,   

    FOREIGN KEY (url_id) REFERENCES urls(id) ON DELETE CASCADE  -- enforces pointer relationship at the database level-> the value in url_id must exist in the id column of the urls table-> this is how we connect the two tables
);                                   

