import time 
import requests 
import os

MEXC_KLINE_URL = "https://api.mexc.com/api/v3/klines"
PAIRS = ["DOGEUSDT", "XRPUSDT", "AAVEUSDT", "HYPEUSDT", "ETHUSDT", "PENGUUSDT"]

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TIMEFRAMES = {
    "15m": "15m",
    "4h": "4h",
    "1d": "1d",
    "1w": "1w"
}

def get_klines(symbol, interval="15m", limit=30):
    url = f"{MEXC_KLINE_URL}?symbol={symbol}&interval={interval}&limit={limit}"
    res = requests.get(url)
    return res.json()

def analyze_trend(symbol, interval):
    try:
        klines = get_klines(symbol, interval=interval)
        closes = [float(k[4]) for k in klines]  # closing prices
        swing_low = min(closes)
        swing_high = max(closes)
        last_price = closes[-1]

        if last_price > swing_high and closes[-2] <= swing_high:
            return "LONG"
        elif last_price < swing_low and closes[-2] >= swing_low:
            return "SHORT"
        else:
            return None
    except:
        return None

def analyze_signal(symbol, interval, direction):
    try:
        klines = get_klines(symbol, interval=interval)
        closes = [float(k[4]) for k in klines]

        swing_low = min(closes)
        swing_high = max(closes)
        last_price = closes[-1]

        fib_0_5 = swing_low + 0.5 * (swing_high - swing_low)
        fib_1_0 = swing_high + (swing_high - swing_low)
        fib_1_618 = swing_high + 1.618 * (swing_high - swing_low)

        fib_0_382 = swing_high - 0.382 * (swing_high - swing_low)
        fib_n1_0 = swing_low - (swing_high - swing_low)
        fib_n1_618 = swing_low - 1.618 * (swing_high - swing_low)

        if direction == "LONG":
            entry = fib_0_5
            sl = swing_low
            tp1 = fib_1_0
            tp2 = fib_1_618
            return {
                "symbol": symbol,
                "side": "LONG",
                "interval": interval,
                "entry": round(entry, 6),
                "sl": round(sl, 6),
                "tp": [round(tp1, 6), round(tp2, 6)],
                "confidence": "HIGH",
                "cta": f"✅ Konfirmasi MULTI-TF arah {direction}. Entry pullback ke Fibo 0.5. SL di bawah swing low. TP bertahap."
            }
        elif direction == "SHORT":
            entry = fib_0_382
            sl = swing_high
            tp1 = fib_n1_0
            tp2 = fib_n1_618
            return {
                "symbol": symbol,
                "side": "SHORT",
                "interval": interval,
                "entry": round(entry, 6),
                "sl": round(sl, 6),
                "tp": [round(tp1, 6), round(tp2, 6)],
                "confidence": "HIGH",
                "cta": f"🔻 Konfirmasi MULTI-TF arah {direction}. Entry pullback ke Fibo 0.382. SL di atas swing high. TP bertahap."
            }
    except:
        return None

def send_to_telegram(signal):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    message = (
        f"🔥 MASTER CALL: {signal['symbol']} – {signal['side']} [{signal['interval'].upper()}]\n"
        f"📍 Entry: {signal['entry']}\n"
        f"🛑 SL: {signal['sl']}\n"
        f"🎯 TP1: {signal['tp'][0]} | TP2: {signal['tp'][1]}\n"
        f"✅ {signal['cta']}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=payload)

def main():
    while True:
        for sym in PAIRS:
            trend_15m = analyze_trend(sym, "15m")
            trend_4h = analyze_trend(sym, "4h")
            trend_1d = analyze_trend(sym, "1d")
            trend_1w = analyze_trend(sym, "1w")

            trends = [trend_15m, trend_4h, trend_1d, trend_1w]
            trends_filtered = [t for t in trends if t is not None]

            if len(trends_filtered) >= 3 and trends_filtered.count(trends_filtered[0]) == len(trends_filtered):
                signal = analyze_signal(sym, "15m", trends_filtered[0])
                if signal:
                    send_to_telegram(signal)
        time.sleep(300)

if __name__ == "__main__":
    main()
