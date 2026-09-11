# bot.py - FINAL BOX B STRATEGY - WITH stocks.py
import yfinance as yf
import pandas as pd
import requests, os, time
from datetime import datetime
import pytz
from stocks import ALL_STOCKS

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TIMEFRAME = os.getenv("TIMEFRAME", "5m")
CHANNEL_WIDTH = int(os.getenv("CHANNEL_WIDTH", "3"))
PERIOD = os.getenv("PERIOD", "5d")

print(f"SETTINGS -> Timeframe: {TIMEFRAME}, Period: {PERIOD}, Width: {CHANNEL_WIDTH}%", flush=True)
print(f"Total Stocks to Scan: {len(ALL_STOCKS)}", flush=True)

def is_market_open():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    if now.weekday() >= 5:
        print(f"Weekend {now} - No Scan", flush=True)
        return False
    start = now.replace(hour=9, minute=15, second=0)
    end = now.replace(hour=15, minute=35, second=0)
    if not (start <= now <= end):
        print(f"Market Closed {now.strftime('%I:%M %p')} - No Scan", flush=True)
        return False
    return True

def send(msg):
    try:
        print(f"Sending: {msg[:80]}", flush=True)
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        print(f"Telegram response: {r.status_code}", flush=True)
    except Exception as e:
        print(f"Send Error: {e}", flush=True)

def get_box_b(df):
    PIVOT_LEN = 20
    pivots = []
    for i in range(PIVOT_LEN, len(df)-PIVOT_LEN):
        if df['High'].iloc[i] == df['High'].iloc[i-PIVOT_LEN:i+PIVOT_LEN+1].max():
            pivots.append(df['High'].iloc[i])
        if df['Low'].iloc[i] == df['Low'].iloc[i-PIVOT_LEN:i+PIVOT_LEN+1].min():
            pivots.append(df['Low'].iloc[i])
    pivots = pivots[-50:]
    if len(pivots) < 6:
        return None
    cwidth = (df['High'].tail(300).max() - df['Low'].tail(300).min()) * CHANNEL_WIDTH / 100
    boxes = []
    temp = pivots.copy()
    for _ in range(10):
        if not temp:
            break
        hi = temp[0]
        cluster = [p for p in temp if abs(p-hi) <= cwidth]
        if cluster:
            boxes.append((min(cluster), max(cluster)))
            temp = [p for p in temp if p not in cluster]
    boxes = sorted(boxes, key=lambda x: (x[0]+x[1])/2)[:6]
    if len(boxes) < 4:
        return None
    return boxes[1][0], boxes[1][1], boxes[-2][0], boxes[-2][1]

if not is_market_open():
    exit(0)

print(f"Market OPEN - Scanning {len(ALL_STOCKS)} stocks - BOX B...", flush=True)

try:
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": f"✅ *BOX B Bot Started* [{TIMEFRAME}] - Scanning {len(ALL_STOCKS)} stocks", "parse_mode": "Markdown"}, timeout=10)
except:
    pass

for sym in ALL_STOCKS:
    try:
        df = yf.Ticker(sym).history(period=PERIOD, interval=TIMEFRAME, auto_adjust=True)
        if df.empty or len(df) < 150:
            print(f"{sym}: No data {len(df)}", flush=True)
            time.sleep(0.2)
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        res = get_box_b(df)
        if not res:
            time.sleep(0.2)
            continue
        b_lo, b_hi, s_lo, s_hi = res
        last = df['Close'].iloc[-1]
        prev = df['Close'].iloc[-2]
        if prev <= b_hi and last > b_hi:
            send(f"🔥 *BOX B BREAKOUT* [{TIMEFRAME}]\n`{sym}`\nLTP: {last:.2f}\nBox: {b_lo:.2f}-{b_hi:.2f}")
        elif prev >= s_lo and last < s_lo:
            send(f"🔻 *BOX B BREAKDOWN* [{TIMEFRAME}]\n`{sym}`\nLTP: {last:.2f}\nBox: {s_lo:.2f}-{s_hi:.2f}")
        time.sleep(0.3)
    except Exception as e:
        print(f"Error {sym}: {e}", flush=True)
        time.sleep(0.3)
        continue

print("Scan Complete - BOX B", flush=True)
