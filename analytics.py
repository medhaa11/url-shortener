from database import get_connection


def get_clicks_over_time(url_id: int):
   
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            DATE(clicked_at) as day,
            COUNT(*)         as total
        FROM clicks
        WHERE url_id = ?
          AND clicked_at >= DATE('now', '-30 days')
        GROUP BY DATE(clicked_at)
        ORDER BY day ASC
        """,
        (url_id,)
    ).fetchall()

    conn.close()

    # Convert to plain lists so Chart.js can use them
    labels = [row["day"]   for row in rows]
    data   = [row["total"] for row in rows]

    return {"labels": labels, "data": data}


def get_device_breakdown(url_id: int):
   
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT device, COUNT(*) as total
        FROM clicks
        WHERE url_id = ?
        GROUP BY device
        ORDER BY total DESC
        """,
        (url_id,)
    ).fetchall()

    conn.close()
    return [{"device": row["device"], "total": row["total"]} for row in rows]


def get_referrer_breakdown(url_id: int):
   
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT referrer, COUNT(*) as total
        FROM clicks
        WHERE url_id = ?
        GROUP BY referrer
        ORDER BY total DESC
        LIMIT 5
        """,
        (url_id,)
    ).fetchall()

    conn.close()
    return [{"referrer": row["referrer"], "total": row["total"]} for row in rows]


def get_summary(url_id: int):
   
    conn = get_connection()

    total = conn.execute(
        "SELECT COUNT(*) as n FROM clicks WHERE url_id = ?",
        (url_id,)
    ).fetchone()["n"]

    today = conn.execute(
        """
        SELECT COUNT(*) as n FROM clicks
        WHERE url_id = ?
          AND DATE(clicked_at) = DATE('now')
        """,
        (url_id,)
    ).fetchone()["n"]

    this_week = conn.execute(
        """
        SELECT COUNT(*) as n FROM clicks
        WHERE url_id = ?
          AND clicked_at >= DATE('now', '-7 days')
        """,
        (url_id,)
    ).fetchone()["n"]

    conn.close()
    return {"total": total, "today": today, "this_week": this_week}
