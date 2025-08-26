#--- moj token = 8281898782:AAHef7o0eUhk8g4JNDpqEwKp4Pi7uhXT64E
#--- moj chat id = 6741354547

import requests

# --- 🔹 Telegram Settings ---
TELEGRAM_TOKEN = "8281898782:AAHef7o0eUhk8g4JNDpqEwKp4Pi7uhXT64E"
CHAT_ID = "6741354547"

# --- 🔹 Spread Threshold (%) ---
MIN_SPREAD = 5  # Only alert if spread >= 5%

# --- 🔹 APIs ---
COINGECKO = "https://api.coingecko.com/api/v3"
BINANCE = "https://api.binance.com/api/v3/ticker/price"
KUCOIN = "https://api.kucoin.com/api/v1/market/orderbook/level1"
KRAKEN = "https://api.kraken.com/0/public/Ticker"


# --- Send Telegram Message ---
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)


# --- Step 1: Get most volatile coin ---
def get_top_volatile_coins(n=5):
    url = f"{COINGECKO}/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 50,
        "page": 1,
        "sparkline": False
    }
    data = requests.get(url, params=params).json()

    coins_with_vol = []
    for coin in data:
        if coin["high_24h"] and coin["low_24h"]:
            avg = (coin["high_24h"] + coin["low_24h"]) / 2
            vol = (coin["high_24h"] - coin["low_24h"]) / avg
            coins_with_vol.append((coin, vol))

    # Sort by volatility descending
    coins_with_vol.sort(key=lambda x: x[1], reverse=True)
    
    # Return top N coins
    return [coin for coin, vol in coins_with_vol[:n]]


# --- Step 2: Get prices from exchanges ---
def get_binance_price(symbol):
    try:
        resp = requests.get(BINANCE, params={"symbol": symbol.upper() + "USDT"})
        return float(resp.json()["price"])
    except:
        return None

def get_kucoin_price(symbol):
    try:
        resp = requests.get(KUCOIN, params={"symbol": symbol.upper() + "-USDT"})
        return float(resp.json()["data"]["price"])
    except:
        return None

def get_kraken_price(symbol):
    try:
        pair = "X" + symbol.upper() + "ZUSD" if symbol.upper() == "BTC" else symbol.upper() + "USD"
        resp = requests.get(KRAKEN, params={"pair": pair})
        result = resp.json()["result"]
        key = list(result.keys())[0]
        return float(result[key]["c"][0])
    except:
        return None
    
def get_coingecko_price(symbol):
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": symbol.lower(),
        "vs_currencies": "usd"
    }
    try:
        resp = requests.get(url, params=params).json()
        return resp[symbol.lower()]["usd"]
    except:
        return None


# --- Analyze a single coin ---
def analyze_coin(coin):
    symbol = coin["symbol"].upper()
    name = coin["name"]

    prices = {}
    prices["Binance"] = get_binance_price(symbol)
    prices["KuCoin"] = get_kucoin_price(symbol)
    prices["Kraken"] = get_kraken_price(symbol)
    prices["CoinGecko"] = get_coingecko_price(coin["id"])

    prices = {k: v for k, v in prices.items() if v is not None}

    if len(prices) < 2:
        print(f"Not enough exchange data for {name} ({symbol})")
        return

    max_price = max(prices.values())
    min_price = min(prices.values())
    spread = (max_price - min_price) / min_price * 100

    if spread >= MIN_SPREAD:
        msg = f"🚨 Volatile Coin Alert 🚨\n\n" \
              f"{name} ({symbol})\n" \
              f"Prices: {prices}\n" \
              f"Spread: {spread:.2f}%"
        print(msg)
        send_telegram(msg)
        print("Alert sent ✅")
    else:
        print(f"{name} ({symbol}) spread is {spread:.2f}%, below threshold.")


# --- Main loop for top N coins ---
if __name__ == "__main__":
    top_coins = get_top_volatile_coins(5)  # Get top 5 volatile coins
    for coin in top_coins:
        analyze_coin(coin)