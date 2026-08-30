# fno-scanner.py - FIXED - Market Hours + No Spam After Close
import yfinance as yf
import pandas as pd
import requests, os, time
from datetime import datetime
import pytz

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

FNO_180 = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS","ITC.NS","LT.NS","KOTAKBANK.NS","AXISBANK.NS","BAJFINANCE.NS","MARUTI.NS","ASIANPAINT.NS","WIPRO.NS","HCLTECH.NS","ULTRACEMCO.NS","TITAN.NS","SUNPHARMA.NS","POWERGRID.NS","NTPC.NS","ONGC.NS","TATASTEEL.NS","JSWSTEEL.NS","ADANIENT.NS","ADANIPORTS.NS","GRASIM.NS","DIVISLAB.NS","DRREDDY.NS","CIPLA.NS","BRITANNIA.NS","EICHERMOT.NS","HEROMOTOCO.NS","BAJAJ-AUTO.NS","M&M.NS","TECHM.NS","BPCL.NS","INDUSINDBK.NS","VEDL.NS","HINDUNILVR.NS","NESTLEIND.NS","HINDALCO.NS","COALINDIA.NS","UPL.NS","TATAMOTORS.NS","BAJAJFINSV.NS","SBILIFE.NS","HDFCLIFE.NS","ICICIPRULI.NS","SHREECEM.NS","PIDILITIND.NS","GODREJCP.NS","DABUR.NS","HAVELLS.NS","BERGEPAINT.NS","MARICO.NS","COLPAL.NS","UBL.NS","MCDOWELL-N.NS"]

def is_market_open():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    # Weekend check
    if now.weekday() >= 5:
        print(f"Weekend - {now} - No Scan")
        return False
    # Market Time 9:15 to 15:35 IST
    start = now.replace(hour=9, minute=15, second=0)
    end = now.replace(hour=15, minute=35, second=0)
    if not (start <= now <= end):
        print(f"Market Closed - {now.strftime('%I:%M %p')} IST - No Scan")
        return False
    return True

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Send fail: {e}")

# MAIN CHECK - Agar market band hai to script yahi exit
if not is_market_open():
    exit(0)

print(f"Market OPEN - Scanning {len(FNO_180)} stocks...")

for sym in FNO_180:
    try:
        # Yahoo block se bachne ke liye session
        df = yf.download(sym, period="5d", interval="5m", progress=False, auto_adjust=True, timeout=10)
        if len(df) < 100: 
            time.sleep(0.8)
            continue
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)
        
        # Tumhara 1% Move Filter
        try:
            mov = (df.tail(78)['High'].max() - df.tail(78)['Low'].min()) / df['Open'].iloc[-78] * 100
        except:
            mov = 0
        if mov < 1.0: 
            time.sleep(0.8)
            continue
        
        # Volume Filter
        if df['Volume'].iloc[-1] < df['Volume'].tail(20).mean()*1.5: 
            time.sleep(0.8)
            continue
        
        # Breakout Logic
        high_20 = df['High'].tail(20).max()
        low_20 = df['Low'].tail(20).min()
        last = df['Close'].iloc[-1]

        if last > float(high_20):
            send(f"🟢 *LONG* {sym}\nMove: {mov:.2f}%\nPrice: {last:.2f}\nBreakout: {float(high_20):.2f}")
        elif last < float(low_20):
            send(f"🔴 *SHORT* {sym}\nMove: {mov:.2f}%\nPrice: {last:.2f}\nBreakdown: {float(low_20):.2f}")

        time.sleep(1.2) # Yahoo block se bachne ke liye 1.2 sec delay MUST

    except Exception as e:
        print(f"Error {sym}: {e}")
        time.sleep(1)
        continue

print("Scan Done")
