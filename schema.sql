-- This file defines the structure of your database
-- Run this once to create your tables

-- The urls table — stores every shortened URL
CREATE TABLE IF NOT EXISTS urls (
    -- INTEGER PRIMARY KEY = auto-incrementing ID (1, 2, 3...)
    -- This ID is what gets Base62 encoded into your short code
    id          INTEGER PRIMARY KEY AUTOINCREMENT,

    -- The short code e.g "aB3xQ" — must be unique, can't be empty
    short_code  TEXT UNIQUE NOT NULL,

    -- The original long URL the user submitted
    original_url TEXT NOT NULL,

    -- Automatically set to current time when row is created
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP,

    -- Optional — for expiring links. NULL means never expires
    expires_at  TEXT
);

-- The clicks table — one row per click on any short link
CREATE TABLE IF NOT EXISTS clicks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Which URL was clicked — links back to urls.id
    -- This is a foreign key — like a pointer to the urls table
    url_id      INTEGER NOT NULL,

    clicked_at  TEXT DEFAULT CURRENT_TIMESTAMP,

    -- Who clicked it
    ip_address  TEXT,
    country     TEXT,
    device      TEXT,   -- "mobile", "desktop", or "tablet"
    referrer    TEXT,   -- where they came from e.g "google.com"

    -- This enforces the foreign key relationship
    -- If a url is deleted, its clicks are deleted too
    FOREIGN KEY (url_id) REFERENCES urls(id) ON DELETE CASCADE  -- enforces pointer relationship at the database level-> the value in url_id must exist in the id column of the urls table-> this is how we connect the two tables
);                                   -- if u delete a url, all its clicks get deleted too

