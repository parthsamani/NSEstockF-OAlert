# bot.py - FINAL LOCKED 5m - LIVE NSE F&O FETCH + BOX B + HIGH PROB
import yfinance as yf
import pandas as pd
import requests, os, logging, asyncio
from datetime import datetime
import pytz
from flask import Flask
from threading import Thread
from telegram.ext import Application

TOKEN = os.getenv("TOKEN") or os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID") or os.getenv("CHANNEL_ID")

# --- LOCKED SETTINGS 5m ---
TIMEFRAME = "5m" # Fixed 5 min
PERIOD = "5d" # Fixed 5 day
CHANNEL_WIDTH = 3
VOLUME_MULT = 1.0
MOVEMENT_MIN = 0.3
NEAR_PCT = 1.0

app = Flask(__name__)
@app.route('/')
def home(): return f"LIVE NSE F&O Scanner Active! TF:{TIMEFRAME}"
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

logging.basicConfig(level=logging.INFO)
sent = set()

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
})

def get_live_fno_list():
    try:
        session.get("https://www.nseindia.com", timeout=15)
        url = "https://www.nseindia.com/api/equities-stockIndices?index=SECURITIES%20IN%20F%26O"
        r = session.get(url, timeout=15)
        data = r.json()
        stocks = [f"{d['symbol']}.NS" for d in data['data']]
        logging.info(f"NSE Live F&O: {len(stocks)} stocks")
        return stocks
    except Exception as e:
        logging.error(f"NSE fail {e}")
        return ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS","POLICYBZR.NS","PAYTM.NS","ZOMATO.NS","TATAMOTORS.NS","TATASTEEL.NS","ADANIENT.NS","BAJFINANCE.NS","DLF.NS","ITC.NS","LT.NS","ONGC.NS","POWERGRID.NS","NTPC.NS","JSWSTEEL.NS","HINDALCO.NS","VEDL.NS","INDIGO.NS","BHEL.NS","BEL.NS","BANKBARODA.NS","PNB.NS","CANBK.NS","IDEA.NS","HINDPETRO.NS"]

def is_market_open():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    if now.weekday() >= 5: return False
    return now.replace(hour=9, minute=15) <= now <= now.replace(hour=15, minute=35)

def get_box_b(df):
    pivots=[]
    for i in range(20, len(df)-20):
        if df['High'].iloc[i] == df['High'].iloc[i-20:i+21].max(): pivots.append(df['High'].iloc[i])
        if df['Low'].iloc[i] == df['Low'].iloc[i-20:i+21].min(): pivots.append(df['Low'].iloc[i])
    pivots=pivots[-50:]
    if len(pivots)<6: return None
    cwidth=(df['High'].tail(300).max()-df['Low'].tail(300).min())*CHANNEL_WIDTH/100
    boxes=[]; temp=pivots.copy()
    for _ in range(10):
        if not temp: break
        hi=temp[0]
        cluster=[p for p in temp if abs(p-hi)<=cwidth]
        if cluster:
            boxes.append((min(cluster), max(cluster)))
            temp=[p for p in temp if p not in cluster]
    boxes=sorted(boxes, key=lambda x:(x[0]+x[1])/2)[:6]
    if len(boxes)<4: return None
    return boxes[1][0], boxes[1][1], boxes[-2][0], boxes[-2][1]

async def send(bot, msg):
    try: await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
    except:
        try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id":CHAT_ID,"text":msg,"parse_mode":"Markdown"}, timeout=10)
        except: pass

async def scanner(bot):
    ALL_STOCKS = get_live_fno_list()
    last_fetch_date = datetime.now().date()
    while True:
        if not is_market_open():
            await asyncio.sleep(300); continue
        if datetime.now().date()!= last_fetch_date:
            ALL_STOCKS = get_live_fno_list()
            last_fetch_date = datetime.now().date()
        for sym in ALL_STOCKS:
            try:
                df=yf.Ticker(sym).history(period=PERIOD, interval=TIMEFRAME, auto_adjust=True)
                if df.empty or len(df)<150: continue
                if isinstance(df.columns, pd.MultiIndex): df.columns=df.columns.get_level_values(0)
                res=get_box_b(df)
                if not res: continue
                b_lo,b_hi,s_lo,s_hi=res
                last=df['Close'].iloc[-1]; prev=df['Close'].iloc[-2]
                open_p=df['Open'].iloc[-1]
                avg_vol=df['Volume'].tail(20).mean()
                vol_ratio=df['Volume'].iloc[-1]/avg_vol if avg_vol>0 else 0
                mov=abs(last-prev)/prev*100 if prev>0 else 0
                if mov<MOVEMENT_MIN or vol_ratio<VOLUME_MULT: continue
                ist=datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%I:%M %p")
                key_base=f"{sym}_{int(last)}"
                msg=None
                if prev<=b_hi and last>b_hi:
                    side="🟢 CALL" if last>open_p else "BREAKOUT"
                    msg=f"🚀 *{side} | {sym.replace('.NS','')}* [{TIMEFRAME}]\nLTP: `{last:.2f}` Mov:{mov:.1f}% Vol:{vol_ratio:.1f}x\nBox Break: {b_hi:.2f} | ⏰ {ist}\n🎯 CALL SIDE ACTIVE"
                elif prev>=s_lo and last<s_lo:
                    side="🔴 PUT" if last<open_p else "BREAKDOWN"
                    msg=f"💣 *{side} | {sym.replace('.NS','')}* [{TIMEFRAME}]\nLTP: `{last:.2f}` Mov:{mov:.1f}% Vol:{vol_ratio:.1f}x\nBox Break: {s_lo:.2f} | ⏰ {ist}\n🎯 PUT SIDE ACTIVE"
                if msg and key_base not in sent:
                    await send(bot, msg)
                    sent.add(key_base)
                await asyncio.sleep(0.4)
            except: continue
        if len(sent)>2000: sent.clear()
        await asyncio.sleep(60)

async def main():
    Thread(target=run_flask, daemon=True).start()
    appb=Application.builder().token(TOKEN).build()
    await appb.initialize(); await appb.start()
    logging.info(f"Bot Started TF={TIMEFRAME}")
    await scanner(appb.bot)

if __name__=="__main__":
    asyncio.run(main())
