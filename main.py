import time 
import requests 
import os

#=== KONFIGURASI ===

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") 
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") 
MEXC_KLINE_URL = "https://api.mexc.com/api/v3/klines"

PAIRS = ["DOGEUSDT", "XRPUSDT", "AAVEUSDT", "HYPEUSDT", "ETHUSDT", "PENGUUSDT"] 
TIMEFRAMES = ["15m", "4h", "1d", "1w"]

#=== FUNGSI UTILITAS ===

def get_klines(symbol, interval="15m", limit=30): 
    url = f"{MEXC_KLINE_URL}?symbol={symbol}&interval={interval}&limit={limit}" 
    try: 
        res = requests.get(url, timeout=10) 
        return res.json() 
    except: 
            return []

def detect_trend(symbol, interval): 
    klines = get_klines(symbol, interval) 
    if not klines: 
        return None 
    closes = [float(k[4]) for k in klines] 
    high = max(closes) 
    low = min(closes) 
    last = closes[-1] 
    if last > high and closes[-2] <= high: 
        return "LONG" 
    elif last < low and closes[-2] >= low: 
        return "SHORT" 
    return None

def calculate_signal(symbol, tf, direction): 
    klines = get_klines(symbol, tf) 
    if not klines: 
        return None 
    closes = [float(k[4]) for k in klines] 
    low = min(closes) 
    high = max(closes) 
    fib_05 = low + 0.5 * (high - low) 
    fib_ext1 = high + (high - low) 
    fib_ext2 = high + 1.618 * (high - low) 
    fib_shrt = high - 0.382 * (high - low) 
    fib_s1 = low - (high - low) 
    fib_s2 = low - 1.618 * (high - low)

if direction == "LONG":
    return {
        "symbol": symbol,
        "side": direction,
        "interval": tf,
        "entry": round(fib_05, 6),
        "sl": round(low, 6),
        "tp": [round(fib_ext1, 6), round(fib_ext2, 6)],
        "cta": "✅ Entry di zona pullback 0.5 Fibo. SL di bawah swing low. TP bertahap."
    }
elif direction == "SHORT":
    return {
        "symbol": symbol,
        "side": direction,
        "interval": tf,
        "entry": round(fib_shrt, 6),
        "sl": round(high, 6),
        "tp": [round(fib_s1, 6), round(fib_s2, 6)],
        "cta": "🔻 Entry setelah breakdown. SL di atas swing high. TP bertahap."
    }
return None

def send_to_telegram(signal):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID: 
        print("[!] TELEGRAM TOKEN/CHAT_ID belum diatur.") 
        return 
    msg = ( 
        f"🔥 MASTER CALL: {signal['symbol']} – {signal['side']} [{signal['interval'].upper()}]\n" 
        f"📍 Entry: {signal['entry']}\n" 
        f"🛑 SL: {signal['sl']}\n" 
        f"🎯 TP1: {signal['tp'][0]} | TP2: {signal['tp'][1]}\n" 
        f"{signal['cta']}" 
    ) 
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage" 
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try: 
        requests.post(url, data=payload, timeout=10) 
        print(f"[✔] Alert dikirim: {signal['symbol']} {signal['side']} [{signal['interval']}]") 
    except Exception as e: 
        print("[x] Gagal kirim Telegram:", e)

#=== LOOP UTAMA ===

def main():
    while True:
        for symbol in PAIRS:
            trends = [detect_trend(symbol, tf) for tf in TIMEFRAMES] 
            valid = [t for t in trends if t is not None] 
            if len(valid) >= 3 and valid.count(valid[0]) == len(valid): 
                signal = calculate_signal(symbol, "15m", valid[0]) 
                if signal: 
                    send_to_telegram(signal) 
        time.sleep(300)  # cek tiap 5 menit

if __name__ == "__main__":
    main()

