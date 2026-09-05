# bot.py - FINAL BOX B STRATEGY - NSEstockF-OAlert
import yfinance as yf
import pandas as pd
import requests, os, time
from datetime import datetime
import pytz

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# --- 179 FNO + 400 Non-FNO = 579 (Unique 499) ---
FNO = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS","ITC.NS","LT.NS","KOTAKBANK.NS","AXISBANK.NS","BAJFINANCE.NS","MARUTI.NS","ASIANPAINT.NS","WIPRO.NS","HCLTECH.NS","ULTRACEMCO.NS","TITAN.NS","SUNPHARMA.NS","POWERGRID.NS","NTPC.NS","ONGC.NS","TATASTEEL.NS","JSWSTEEL.NS","ADANIENT.NS","ADANIPORTS.NS","GRASIM.NS","DIVISLAB.NS","DRREDDY.NS","CIPLA.NS","BRITANNIA.NS","EICHERMOT.NS","HEROMOTOCO.NS","BAJAJ-AUTO.NS","M&M.NS","TECHM.NS","BPCL.NS","INDUSINDBK.NS","VEDL.NS","HINDUNILVR.NS","NESTLEIND.NS","HINDALCO.NS","COALINDIA.NS","UPL.NS","TATAMOTORS.NS","BAJAJFINSV.NS","SBILIFE.NS","HDFCLIFE.NS","ICICIPRULI.NS","SHREECEM.NS","PIDILITIND.NS","GODREJCP.NS","DABUR.NS","HAVELLS.NS","BERGEPAINT.NS","MARICO.NS","COLPAL.NS","UBL.NS","MCDOWELL-N.NS","DLF.NS","GODREJPROP.NS","INDIGO.NS","ZOMATO.NS","DIXON.NS","POLYCAB.NS","SIEMENS.NS","ABB.NS","BHEL.NS","HAL.NS","BEL.NS","RECLTD.NS","PFC.NS","CHOLAFIN.NS","BANKBARODA.NS","PNB.NS","TRENT.NS","PIDILITIND.NS","SRF.NS","LTIM.NS","PERSISTENT.NS","COFORGE.NS","MOTHERSON.NS"]

NON_FNO = ["BSE.NS","CDSL.NS","KFINTECH.NS","360ONE.NS","NUVAMA.NS","ANANDRATHI.NS","MOTILALOFS.NS","ANGELONE.NS","CAMS.NS","MCX.NS","IEX.NS","KPITTECH.NS","TATACHEM.NS","DEEPAKNTR.NS","AARTIIND.NS","ATUL.NS","KALYANKJIL.NS","SAGILITY.NS","ATHERENERG.NS","MAHABANK.NS","BANKOFBARODA.NS","CANBK.NS","MAZDOCK.NS","COCHINSHIP.NS","IDEA.NS","IRCTC.NS","IRFC.NS","RVNL.NS","HUDCO.NS","NBCC.NS","OIL.NS","GAIL.NS","IGL.NS","MGL.NS","ASTRAL.NS","KAJARIACER.NS","CERA.NS","TITAN.NS","DMART.NS","TRENT.NS","ABFRL.NS","PAGEIND.NS","VBL.NS","TITAGARH.NS","BHEL.NS","HAL.NS","BDL.NS","KAYNES.NS","DIXON.NS","AMBER.NS","CGPOWER.NS","SUZLON.NS","TATAPOWER.NS","JSWENERGY.NS","TATATECH.NS","SONACOMS.NS","M&MFIN.NS","PEL.NS","BSE.NS","CDSL.NS","DELHIVERY.NS","AWL.NS","ADANIWIL.NS","JINDALSTEL.NS","SAIL.NS","NMDC.NS","HINDZINC.NS","NATIONALUM.NS","JSL.NS","APLAPOLLO.NS","EIH.NS","INDHOTEL.NS","LEMONTREE.NS","BRIGADE.NS","PRESTIGE.NS","SOBHA.NS","PHOENIXLTD.NS","TCS.NS","INFY.NS","WIPRO.NS","LTIM.NS","TECHM.NS","HCLTECH.NS","MPHASIS.NS","KPITTECH.NS","TATAELXSI.NS","LTTS.NS","CYIENT.NS","BSOFT.NS","MASTEK.NS","ROUTE.NS","AFFLE.NS","TANLA.NS","VODAFONE.NS","INDUSINDBK.NS","FEDERALBNK.NS","KOTAKBANK.NS","PNB.NS","BANDHANBNK.NS","AUBANK.NS","IDFCFIRSTB.NS","EQUITASBNK.NS","JUBLFOOD.NS","DEVYANI.NS","DOMS.NS","STYLAM.NS","CENTURYPLY.NS","KAJARIACER.NS","ASIANPAINT.NS","BERGEPAINT.NS","PIDILITIND.NS","SRF.NS","ATUL.NS","AARTIIND.NS","DEEPAKNTR.NS","NAVINFLUOR.NS","TATACHEM.NS","SUNPHARMA.NS","DIVISLAB.NS","CIPLA.NS","DRREDDY.NS","LUPIN.NS","AUROPHARMA.NS","ZYDUSLIFE.NS","ALKEM.NS","TORNTPHARM.NS","GLENMARK.NS","IPCALAB.NS","LAURUSLABS.NS","SYNGENE.NS","METROPOLIS.NS","LALPATHLAB.NS","KRSNAA.NS","MEDANTA.NS","FORTIS.NS","APOLLOHOSP.NS","MAXHEALTH.NS","STARHEALTH.NS","ICICIGI.NS","SBICARD.NS"]

ALL_STOCKS = list(dict.fromkeys(FNO + NON_FNO))

def is_market_open():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    if now.weekday() >= 5: return False
    start = now.replace(hour=9, minute=15, second=0)
    end = now.replace(hour=15, minute=35, second=0)
    return start <= now <= end

def send(msg):
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_box_b(df):
    PIVOT_LEN = 50
    pivots = []
    for i in range(PIVOT_LEN, len(df)-PIVOT_LEN):
        if df['High'].iloc[i] == df['High'].iloc[i-PIVOT_LEN:i+PIVOT_LEN+1].max(): pivots.append(df['High'].iloc[i])
        if df['Low'].iloc[i] == df['Low'].iloc[i-PIVOT_LEN:i+PIVOT_LEN+1].min(): pivots.append(df['Low'].iloc[i])
    pivots = pivots[-50:]
    if len(pivots) < 6: return None
    cwidth = (df['High'].tail(300).max() - df['Low'].tail(300).min()) * 5 / 100
    boxes = []
    temp = pivots.copy()
    for _ in range(10):
        if not temp: break
        hi = temp[0]
        cluster = [p for p in temp if abs(p-hi) <= cwidth]
        if cluster:
            boxes.append((min(cluster), max(cluster)))
            temp = [p for p in temp if p not in cluster]
    boxes = sorted(boxes, key=lambda x: (x[0]+x[1])/2)[:6]
    if len(boxes) < 6: return None
    return boxes[1][0], boxes[1][1], boxes[-2][0], boxes[-2][1] # buyB_lo, hi, sellB_lo, hi

if not is_market_open():
    print("Market Closed")
    exit(0)

print(f"Scanning {len(ALL_STOCKS)} stocks - BOX B...")
for sym in ALL_STOCKS:
    try:
        df = yf.download(sym, period="20d", interval="15m", progress=False, auto_adjust=True, timeout=15)
        if len(df) < 150:
            time.sleep(0.5); continue
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        res = get_box_b(df)
        if not res:
            time.sleep(0.5); continue
        b_lo, b_hi, s_lo, s_hi = res
        last = df['Close'].iloc[-1]; prev = df['Close'].iloc[-2]
        if prev <= b_hi and last > b_hi:
            send(f"🔥 *BOX B BREAKOUT*\n`{sym}`\nLTP: {last:.2f}\nBox: {b_lo:.2f}-{b_hi:.2f}")
        elif prev >= s_lo and last < s_lo:
            send(f"🔻 *BOX B BREAKDOWN*\n`{sym}`\nLTP: {last:.2f}\nBox: {s_lo:.2f}-{s_hi:.2f}")
        time.sleep(0.8)
    except Exception as e:
        print(e); time.sleep(1); continue
print("Done")
