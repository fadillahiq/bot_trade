import time
import requests
from discord_webhook import DiscordWebhook, DiscordEmbed

MEXC_KLINE_URL = "https://api.mexc.com/api/v3/klines"
PAIRS = ["DOGEUSDT", "XRPUSDT", "AAVEUSDT", "HYPEUSDT", "ETHUSDT", "PENGUUSDT"]
WEBHOOK_URL = "https://discord.com/api/webhooks/1396241622894907562/2Hpd4F4IAyUS9GQU4ybJoZXQMDRCsKEgnOo9d1OLdI8DOmewcwP-T1ntMmzi69TjIhNs"

TIMEFRAMES = {
    "15m": "15m",
    "4h": "4h", 
    "1d": "1d",
    "1w": "1W"
}

def get_klines(symbol, interval="15m", limit=30):
    try:
        # Use proper interval format for MEXC API
        if interval == "1w":
            interval = "1W"
        
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        res = requests.get(MEXC_KLINE_URL, params=params, timeout=10)
        
        if res.status_code == 400:
            print(f"Bad request for {symbol} with interval {interval}. Trying alternative intervals...")
            # Try alternative intervals if the requested one fails
            alternative_intervals = ["1d", "4h", "15m"]
            for alt_interval in alternative_intervals:
                if alt_interval != interval:
                    alt_params = params.copy()
                    alt_params['interval'] = alt_interval
                    alt_res = requests.get(MEXC_KLINE_URL, params=alt_params, timeout=10)
                    if alt_res.status_code == 200:
                        print(f"Using {alt_interval} instead of {interval} for {symbol}")
                        return alt_res.json()
            return None
            
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"Error fetching klines for {symbol}: {e}")
        return None

def analyze_trend(symbol, interval):
    try:
        klines = get_klines(symbol, interval=interval)
        if not klines or len(klines) < 2:
            return None
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
    except Exception as e:
        print(f"Error analyzing trend for {symbol} {interval}: {e}")
        return None

def analyze_signal(symbol, interval, direction):
    try:
        klines = get_klines(symbol, interval=interval)
        if not klines or len(klines) == 0:
            return None
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
    except Exception as e:
        print(f"Error analyzing signal for {symbol} {interval}: {e}")
        return None

def send_to_discord(signal):
    try:
        webhook = DiscordWebhook(url=WEBHOOK_URL)
        send_to_telegram(
    message=f"🔥 *MASTER CALL: {signal['symbol']} – {signal['side']} [{signal['interval'].upper()}]*\n"
            f"📍 Entry: {signal['entry']}\n"
            f"🛑 SL: {signal['sl']}\n"
            f"🎯 TP1: {signal['tp'][0]} | TP2: {signal['tp'][1]}\n"
            f"✅ {signal['cta']}",
    token="7580552170:AAEGs8Z4HVhZgtnzRaK4VctZe6_fUL0pkz8",
    chat_id="5246334675"
        )
        embed = DiscordEmbed(
            title=f"🔥 MASTER CALL: {signal['symbol']} – {signal['side']} [{signal['interval'].upper()}]",
            color="03b2f8"
        )
        embed.add_embed_field(name="Entry", value=f"{signal['entry']:.6f}", inline=True)
        embed.add_embed_field(name="Stop Loss", value=f"{signal['sl']:.6f}", inline=True)
        embed.add_embed_field(name="Take Profit", value="\n".join(f"TP{i+1}: {tp:.6f}" for i, tp in enumerate(signal["tp"])), inline=False)
        embed.add_embed_field(name="Confidence", value=signal["confidence"], inline=True)
        embed.set_footer(text=signal["cta"])
        webhook.add_embed(embed)
        response = webhook.execute()
        print(f"Signal sent for {signal['symbol']}: {signal['side']}")
        return response
    except Exception as e:
        print(f"Error sending Discord webhook: {e}")
        return None

def send_to_telegram(message, token, chat_id):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=payload)

def main():
    print("Starting crypto signal bot...")
    while True:
        try:
            print(f"Scanning {len(PAIRS)} pairs at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            for sym in PAIRS:
                print(f"Analyzing {sym}...")
                trend_15m = analyze_trend(sym, "15m")
                trend_4h = analyze_trend(sym, "4h") 
                trend_1d = analyze_trend(sym, "1d")
                trend_1w = analyze_trend(sym, "1W")

                trends = [trend_15m, trend_4h, trend_1d, trend_1w]
                trends_filtered = [t for t in trends if t is not None]

                if len(trends_filtered) >= 3 and trends_filtered.count(trends_filtered[0]) == len(trends_filtered):
                    print(f"Multi-timeframe alignment detected for {sym}: {trends_filtered[0]}")
                    signal = analyze_signal(sym, "15m", trends_filtered[0])
                    if signal:
                        send_to_discord(signal)
                    else:
                        print(f"Failed to generate signal for {sym}")
                
                time.sleep(1)  # Brief pause between symbols to avoid rate limiting
            
            print("Scan complete. Waiting 5 minutes for next scan...")
            time.sleep(300)
        except KeyboardInterrupt:
            print("Bot stopped by user")
            break
        except Exception as e:
            print(f"Unexpected error in main loop: {e}")
            print("Continuing in 30 seconds...")
            time.sleep(30)

if __name__ == "__main__":
    main()
