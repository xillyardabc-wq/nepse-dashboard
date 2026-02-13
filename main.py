from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import pytz
from datetime import datetime

app = FastAPI()
latest_data = {}

SYMBOLS = ["SSHL","HIDCL","NABIL"]

def calculate_score(data):
    score = 0
    ltp = float(data.get("LTP", 0))
    high = float(data.get("High", 0))
    prev = float(data.get("Previous Close", 0))
    volume = float(data.get("Volume", 0))

    if ltp > prev:
        score += 30
    if ltp >= high * 0.98:
        score += 30
    if volume > 50000:
        score += 40

    return min(score, 100)

def fetch_data():
    global latest_data
    for sym in SYMBOLS:
        try:
            res = requests.get(f"https://nepsetty.kokomo.workers.dev/api?symbol={sym}")
            data = res.json()

            score = calculate_score(data)

            latest_data[sym] = {
                "symbol": sym,
                "ltp": data.get("LTP"),
                "volume": data.get("Volume"),
                "score": score,
                "status": "Strong" if score >= 70 else "Moderate"
            }
        except:
            latest_data[sym] = {"error": "Failed"}

scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Kathmandu"))
scheduler.add_job(fetch_data, 'cron', day_of_week='sun-thu', hour=15, minute=1)
scheduler.start()

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
    <html>
    <head>
        <title>NEPSE Smart Dashboard</title>
        <style>
            body { font-family: Arial; background:#f4f6f9; padding:20px; }
            .card { background:white; padding:20px; margin:10px; border-radius:10px; box-shadow:0 2px 8px rgba(0,0,0,0.1);}
            .strong { color:green; font-weight:bold; }
            .moderate { color:orange; }
        </style>
        <script>
            async function loadData(){
                const res = await fetch('/latest');
                const data = await res.json();
                let html = '';
                for (let key in data){
                    let s = data[key];
                    html += `
                        <div class="card">
                            <h2>${s.symbol}</h2>
                            <p>Price: ${s.ltp}</p>
                            <p>Volume: ${s.volume}</p>
                            <p>Score: ${s.score}</p>
                            <p class="${s.score>=70?'strong':'moderate'}">
                                ${s.status}
                            </p>
                        </div>
                    `;
                }
                document.getElementById('data').innerHTML = html;
            }
            setInterval(loadData, 60000);
            window.onload = loadData;
        </script>
    </head>
    <body>
        <h1>📊 NEPSE Smart Money Dashboard</h1>
        <div id="data">Waiting for 3:01 PM update...</div>
    </body>
    </html>
    """

@app.get("/latest")
def latest():
    return latest_data
