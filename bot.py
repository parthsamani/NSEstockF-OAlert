import yfinance as yf
import pandas as pd
import requests, os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

FNO = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS","ITC.NS","LT.NS","KOTAKBANK.NS","AXISBANK.NS","BAJFINANCE.NS","MARUTI.NS","ASIANPAINT.NS","WIPRO.NS","HCLTECH.NS","ULTRACEMCO.NS","TITAN.NS","SUNPHARMA.NS","POWERGRID.NS","NTPC.NS","ONGC.NS","TATASTEEL.NS","JSWSTEEL.NS","ADANIENT.NS","ADANIPORTS.NS","GRASIM.NS","DIVISLAB.NS","DRREDDY.NS","CIPLA.NS","BRITANNIA.NS","EICHERMOT.NS","HEROMOTOCO.NS","BAJAJ-AUTO.NS","M&M.NS","TECHM.NS","BPCL.NS","INDUSINDBK.NS","VEDL.NS"]

def send(msg):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

for sym in FNO:
    try:
        df = yf.download(sym, period="5d", interval="5m", progress=False, auto_adjust=True)
        if len(df) < 100: continue
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        mov = (df.tail(78)['High'].max() - df.tail(78)['Low'].min()) / df['Open'].iloc[-78] * 100
        if mov < 1.0: continue
        if df['Volume'].iloc[-1] < df['Volume'].tail(20).mean()*1.5: continue

        # Simple Breakout logic (Pine Script wala)
        high_20 = df['High'].tail(20).max()
        low_20 = df['Low'].tail(20).min()
        last = df['Close'].iloc[-1]

        if last > high_20:
            send(f"🟢 *LONG* {sym}\nMove: {mov:.2f}%\nPrice: {last:.2f}\nBreakout: {high_20:.2f}")
        elif last < low_20:
            send(f"🔴 *SHORT* {sym}\nMove: {mov:.2f}%\nPrice: {last:.2f}\nBreakdown: {low_20:.2f}")

    except:
        continue
