import sqlite3

DATABASE = "urls.db"


def get_connection():
   
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    
    conn = get_connection()
    with open("schema.sql", "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("Database initialised successfully")


def create_url(original_url: str, short_code: str):
   
    conn = get_connection()

    conn.execute(
        "INSERT INTO urls (short_code, original_url) VALUES (?, ?)",
        (short_code, original_url)
    )
    conn.commit()

    # Fetch and return the full row we just created
    url = conn.execute(
        "SELECT * FROM urls WHERE short_code = ?",
        (short_code,)
    ).fetchone()

    conn.close()
    return url


def get_next_id(original_url: str):
    
    conn = get_connection()

    # Insert with a temporary placeholder
    cursor = conn.execute(
        "INSERT INTO urls (short_code, original_url) VALUES (?, ?)",
        ("placeholder", original_url)
    )
    conn.commit()

    # lastrowid gives us the auto-generated ID from the INSERT above
    new_id = cursor.lastrowid

    conn.close()
    return new_id


def update_short_code(url_id: int, short_code: str):
    
    conn = get_connection()

    conn.execute(
        "UPDATE urls SET short_code = ? WHERE id = ?",
        (short_code, url_id)
    )
    conn.commit()

    # Return the fully updated row
    url = conn.execute(
        "SELECT * FROM urls WHERE id = ?",
        (url_id,)
    ).fetchone()

    conn.close()
    return url


def get_url(short_code: str):
    
    conn = get_connection()

    url = conn.execute(
        "SELECT * FROM urls WHERE short_code = ?",
        (short_code,)
    ).fetchone()

    conn.close()
    return url


def log_click(url_id: int, ip_address: str, referrer: str, device: str):
   
    conn = get_connection()

    conn.execute(
        """
        INSERT INTO clicks (url_id, ip_address, referrer, device)
        VALUES (?, ?, ?, ?)
        """,
        (url_id, ip_address, referrer, device)
    )
    conn.commit()
    conn.close()


def get_click_count(url_id: int):
   
    conn = get_connection()

    result = conn.execute(
        "SELECT COUNT(*) as total FROM clicks WHERE url_id = ?",
        (url_id,)
    ).fetchone()

    conn.close()
    return result["total"]


def get_all_urls():
    
    
    conn = get_connection()

    urls = conn.execute(
        "SELECT * FROM urls ORDER BY created_at DESC" # sorts newest first..ie descending order
    ).fetchall()

    conn.close()
    return urls
