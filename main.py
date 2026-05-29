from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import user_agents
import json
from cache import cache_get, cache_set
from rate_limiter import is_rate_limited
from database import (
    init_db, get_next_id, update_short_code,
    get_url, log_click, get_all_urls
)
from encoder import encode
from analytics import (
    get_clicks_over_time, get_device_breakdown,
    get_referrer_breakdown, get_summary
)

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

def detect_device(user_agent_string: str) -> str:
    ua = user_agents.parse(user_agent_string)
    if ua.is_mobile:
        return "mobile"
    elif ua.is_tablet:
        return "tablet"
    else:
        return "desktop"

# ─────────────────────────────────────────
# HOMEPAGE
# ─────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    urls = get_all_urls()
    base_url = str(request.base_url)

    rows_html = ""
    for url in urls:
        rows_html += f"""
        <div style="background:#111;border:1px solid #222;border-radius:8px;padding:12px 16px;
                    display:flex;align-items:center;justify-content:space-between;gap:16px;">
            <div style="min-width:0;flex:1;">
                <a href="/{url['short_code']}" target="_blank"
                   style="font-family:monospace;font-size:14px;color:#818cf8;font-weight:600;
                          text-decoration:none;display:block;margin-bottom:4px;">
                    {base_url}{url['short_code']}
                </a>
                <span style="font-family:monospace;font-size:11px;color:#475569;
                             white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
                             display:block;max-width:400px;">
                    {url['original_url']}
                </span>
            </div>
            <a href="/dashboard/{url['short_code']}"
               style="font-size:12px;font-weight:600;background:#1e1e2e;color:#94a3b8;
                      padding:6px 14px;border-radius:6px;border:1px solid #2e2e3e;
                      text-decoration:none;white-space:nowrap;">
                Analytics
            </a>
        </div>
        """

    if not rows_html:
        rows_html = """
        <div style="border:1px dashed #222;border-radius:8px;padding:40px;text-align:center;
                    color:#334155;font-size:13px;">
            No links yet. Paste a URL above to create your first short link.
        </div>
        """

    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>URL Shortener</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ background: #0a0a0a; color: #e2e8f0; font-family: sans-serif;
                    min-height: 100vh; }}
            nav {{ border-bottom: 1px solid #1e1e2e; padding: 0 24px; height: 56px;
                   display: flex; align-items: center; justify-content: space-between;
                   background: rgba(10,10,10,0.9); position: sticky; top: 0; z-index: 10; }}
            main {{ max-width: 680px; margin: 0 auto; padding: 48px 24px 96px; }}
        </style>
    </head>
    <body>
        <nav>
            <span style="font-size:16px;font-weight:700;color:#818cf8;">URL Shortener</span>
            <span style="font-size:12px;font-family:monospace;color:#334155;
                         background:#111;border:1px solid #1e1e2e;padding:4px 12px;
                         border-radius:6px;">v1.0</span>
        </nav>
        <main>
            <h1 style="font-size:28px;font-weight:700;margin-bottom:8px;">Shorten a URL</h1>
            <p style="color:#475569;font-size:14px;margin-bottom:32px;">
                Paste any long URL and get a short trackable link.
            </p>

            <div style="background:#111;border:1px solid #1e1e2e;border-radius:12px;
                        padding:20px;margin-bottom:40px;">
                <form action="/shorten" method="POST"
                      style="display:flex;gap:10px;flex-wrap:wrap;">
                    <input type="url" name="url"
                           placeholder="https://your-long-url.com/..."
                           required
                           style="flex:1;min-width:200px;background:#0a0a0a;
                                  border:1px solid #1e1e2e;border-radius:8px;
                                  padding:10px 14px;font-size:13px;color:#e2e8f0;
                                  outline:none;font-family:monospace;">
                    <button type="submit"
                            style="background:#4f46e5;color:#fff;border:none;
                                   border-radius:8px;padding:10px 20px;
                                   font-size:13px;font-weight:600;cursor:pointer;">
                        Shorten
                    </button>
                </form>
            </div>

            <h3 style="font-size:12px;font-weight:700;letter-spacing:2px;
                        text-transform:uppercase;color:#334155;margin-bottom:12px;">
                Your Links
            </h3>
            <div style="display:flex;flex-direction:column;gap:8px;">
                {rows_html}
            </div>
        </main>
    </body>
    </html>
    """)

# ─────────────────────────────────────────
# POST /shorten
# ─────────────────────────────────────────
@app.post("/shorten")
def shorten_url(request: Request, url: str = Form(...)):
    if is_rate_limited(request.client.host):
        return HTMLResponse(
            content="<h1>429 — Too many requests. Wait a minute and try again.</h1>",
            status_code=429
        )
    new_id     = get_next_id(url)
    short_code = encode(new_id)
    update_short_code(new_id, short_code)
    cache_set(short_code, url)
    return RedirectResponse(url="/", status_code=303)

# ─────────────────────────────────────────
# GET /health  <- must be before /{short_code}
# ─────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Server is running"}

# ─────────────────────────────────────────
# GET /dashboard/{short_code}
# ─────────────────────────────────────────
@app.get("/dashboard/{short_code}", response_class=HTMLResponse)
def dashboard(short_code: str, request: Request):
    url = get_url(short_code)
    if not url:
        return HTMLResponse(content="<h1>404 — Link not found</h1>", status_code=404)

    url_id   = url["id"]
    summary  = get_summary(url_id)
    devices  = get_device_breakdown(url_id)
    refs     = get_referrer_breakdown(url_id)
    overtime = get_clicks_over_time(url_id)

    short_url = str(request.base_url) + short_code
    max_ref   = refs[0]["total"] if refs else 1

    chart_labels  = json.dumps(overtime["labels"])
    chart_data    = json.dumps(overtime["data"])
    device_labels = json.dumps([d["device"] for d in devices])
    device_data   = json.dumps([d["total"]  for d in devices])

    ref_rows = ""
    for r in refs:
        pct = int(r["total"] / max_ref * 100)
        label = r["referrer"] if r["referrer"] else "direct / email / sms"
        ref_rows += f"""
        <div style="margin-bottom:14px;">
            <div style="display:flex;justify-content:space-between;
                        font-size:12px;margin-bottom:6px;">
                <span style="font-family:monospace;color:#cbd5e1;">{label}</span>
                <span style="font-family:monospace;color:#475569;">{r['total']} clicks</span>
            </div>
            <div style="background:#0a0a0a;height:4px;border-radius:2px;
                        border:1px solid #1e1e2e;overflow:hidden;">
                <div style="background:#4f46e5;height:100%;width:{pct}%;border-radius:2px;"></div>
            </div>
        </div>
        """

    if not ref_rows:
        ref_rows = "<p style='color:#334155;font-size:13px;text-align:center;padding:20px;'>No referrer data yet.</p>"

    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Analytics - {short_code}</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ background: #0a0a0a; color: #e2e8f0; font-family: sans-serif; min-height: 100vh; }}
            nav {{ border-bottom: 1px solid #1e1e2e; padding: 0 24px; height: 56px;
                   display: flex; align-items: center; justify-content: space-between;
                   background: rgba(10,10,10,0.9); position: sticky; top: 0; z-index: 10; }}
            main {{ max-width: 800px; margin: 0 auto; padding: 32px 24px 96px; }}
            .card {{ background: #111; border: 1px solid #1e1e2e; border-radius: 12px; padding: 20px; }}
        </style>
    </head>
    <body>
        <nav>
            <div style="display:flex;align-items:center;gap:10px;">
                <span style="font-size:16px;font-weight:700;color:#818cf8;">URL Shortener</span>
                <span style="color:#1e1e2e;">/</span>
                <span style="font-family:monospace;font-size:13px;color:#475569;
                             background:#111;border:1px solid #1e1e2e;
                             padding:3px 10px;border-radius:6px;">{short_code}</span>
            </div>
            <a href="/" style="font-size:12px;color:#475569;text-decoration:none;
                               border:1px solid #1e1e2e;padding:5px 12px;border-radius:6px;">
                <- Back
            </a>
        </nav>
        <main>
            <div class="card" style="margin-bottom:16px;">
                <div style="font-size:10px;color:#475569;letter-spacing:2px;
                            text-transform:uppercase;margin-bottom:4px;">Tracking Link</div>
                <a href="/{short_code}" target="_blank"
                   style="font-family:monospace;font-size:15px;color:#818cf8;
                          font-weight:600;text-decoration:none;">{short_url}</a>
                <div style="font-family:monospace;font-size:11px;color:#334155;
                            margin-top:8px;border-top:1px solid #1e1e2e;padding-top:8px;">
                    -> {url['original_url']}
                </div>
            </div>

            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px;">
                <div class="card">
                    <div style="font-size:10px;color:#475569;letter-spacing:2px;
                                text-transform:uppercase;margin-bottom:6px;">Total Clicks</div>
                    <div style="font-size:30px;font-weight:700;font-family:monospace;
                                color:#e2e8f0;">{summary['total']}</div>
                </div>
                <div class="card">
                    <div style="font-size:10px;color:#475569;letter-spacing:2px;
                                text-transform:uppercase;margin-bottom:6px;">Today</div>
                    <div style="font-size:30px;font-weight:700;font-family:monospace;
                                color:#34d399;">{summary['today']}</div>
                </div>
                <div class="card">
                    <div style="font-size:10px;color:#475569;letter-spacing:2px;
                                text-transform:uppercase;margin-bottom:6px;">This Week</div>
                    <div style="font-size:30px;font-weight:700;font-family:monospace;
                                color:#818cf8;">{summary['this_week']}</div>
                </div>
            </div>

            <div style="display:grid;grid-template-columns:3fr 2fr;gap:12px;margin-bottom:16px;">
                <div class="card" id="line-box"
                     data-labels='{chart_labels}' data-values='{chart_data}'>
                    <div style="font-size:10px;color:#475569;letter-spacing:2px;
                                text-transform:uppercase;margin-bottom:16px;">
                        Clicks Over Time (30d)
                    </div>
                    <div style="position:relative;height:200px;">
                        <canvas id="lineChart"></canvas>
                    </div>
                </div>
                <div class="card" id="donut-box"
                     data-labels='{device_labels}' data-values='{device_data}'>
                    <div style="font-size:10px;color:#475569;letter-spacing:2px;
                                text-transform:uppercase;margin-bottom:16px;">
                        Devices
                    </div>
                    <div style="position:relative;height:200px;">
                        <canvas id="donutChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="card">
                <div style="font-size:10px;color:#475569;letter-spacing:2px;
                            text-transform:uppercase;margin-bottom:16px;">
                    Top Referrers
                </div>
                {ref_rows}
            </div>
        </main>

        <script>
            Chart.defaults.color = '#475569';
            Chart.defaults.font.family = 'monospace';

            const lineBox = document.getElementById("line-box");
            const lineLabels = JSON.parse(lineBox.dataset.labels || "[]");
            const lineData   = JSON.parse(lineBox.dataset.values || "[]");

            if (lineLabels.length > 0) {{
                new Chart(document.getElementById("lineChart"), {{
                    type: "line",
                    data: {{
                        labels: lineLabels,
                        datasets: [{{
                            data: lineData,
                            borderColor: "#818cf8",
                            backgroundColor: "rgba(129,140,248,0.05)",
                            borderWidth: 2,
                            pointBackgroundColor: "#818cf8",
                            pointRadius: 3,
                            fill: true,
                            tension: 0.3
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{
                            x: {{ grid: {{ color: '#1e1e2e' }} }},
                            y: {{ beginAtZero: true, grid: {{ color: '#1e1e2e' }},
                                  ticks: {{ precision: 0 }} }}
                        }}
                    }}
                }});
            }}

            const donutBox = document.getElementById("donut-box");
            const deviceLabels = JSON.parse(donutBox.dataset.labels || "[]");
            const deviceData   = JSON.parse(donutBox.dataset.values || "[]");

            if (deviceLabels.length > 0) {{
                new Chart(document.getElementById("donutChart"), {{
                    type: "doughnut",
                    data: {{
                        labels: deviceLabels,
                        datasets: [{{
                            data: deviceData,
                            backgroundColor: ["#818cf8", "#34d399", "#f59e0b"],
                            borderWidth: 3,
                            borderColor: "#111"
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: "bottom",
                                labels: {{ boxWidth: 10, padding: 14, color: '#94a3b8',
                                           font: {{ size: 11 }} }}
                            }}
                        }}
                    }}
                }});
            }}
        </script>
    </body>
    </html>
    """)

# ─────────────────────────────────────────
# GET /{short_code} — wildcard, must be last
# ─────────────────────────────────────────
@app.get("/{short_code}")
def redirect_url(short_code: str, request: Request):
    original_url = cache_get(short_code)

    if original_url:
        ua_string = request.headers.get("user-agent", "")
        device    = detect_device(ua_string)
        url       = get_url(short_code)
        if url:
            log_click(
                url_id=url["id"],
                ip_address=request.client.host,
                referrer=request.headers.get("referer", "direct"),
                device=device
            )
        return RedirectResponse(url=original_url, status_code=302)

    url = get_url(short_code)
    if not url:
        return HTMLResponse(
            content=f"""
            <html>
                <body style="font-family:sans-serif;text-align:center;margin-top:80px;">
                    <h1>404 - Link not found</h1>
                    <p>The short code <strong>{short_code}</strong> doesn't exist.</p>
                    <a href="/">Go back home</a>
                </body>
            </html>
            """,
            status_code=404
        )

    cache_set(short_code, url["original_url"])
    ua_string = request.headers.get("user-agent", "")
    device    = detect_device(ua_string)
    log_click(
        url_id=url["id"],
        ip_address=request.client.host,
        referrer=request.headers.get("referer", "direct"),
        device=device
    )
    return RedirectResponse(url=url["original_url"], status_code=302)