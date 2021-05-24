import ccxt
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

binance = ccxt.binance()

def get_ror(k=0.5):
    ohlcv = binance.fetch_ohlcv("BTC/USDT", limit=2)
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'],
                         1)

    ror = df['ror'].cumprod().iloc[-2]
    return ror

def get_target_price(ticker, k):
    ohlcv = binance.fetch_ohlcv(ticker, '1d', limit=2)
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df['open'] = df['open'].astype(np.float64)
    df['high'] = df['high'].astype(np.float64)
    df['low'] = df['low'].astype(np.float64)
    df['close'] = df['close'].astype(np.float64)
    df['volume'] = df['volume'].astype(np.float64)
    df.set_index('datetime', inplace=True)
    target_price = df['close'][0] + (df['high'][0] - df['low'][0]) * k
    return target_price

def get_current_price(ticker):
    btc = binance.fetch_ticker(ticker)
    return btc['close']
    # return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def get_start_time(ticker):
    ohlcv = binance.fetch_ohlcv(ticker, '1d', limit=1)
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    start_time = df['datetime'][0]
    return start_time

def get_ma15(ticker):
    ohlcv = binance.fetch_ohlcv(ticker, '1d', limit=15)
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15

#orderbook = binance.fetch_order_book('ETH/USDT')
# for bid in orderbook['bids']:
#     print(bid[0], bid[1])
# for ask in orderbook['asks']:
#     print(ask[0], ask[1])
#print(orderbook['bids'][0])
#print(orderbook['asks'][0])

with open("api.txt") as f:
    lines = f.readlines()
    apiKey = lines[0].strip()
    secret = lines[1].strip()

binance = ccxt.binance(config={
    'apiKey': apiKey,
    'secret': secret
})

def get_balance(ticker):
    balance = binance.fetch_balance()
    if balance[ticker]['free'] is not None:
        return float(balance[ticker]['free'])
    else:
        return 0

# for k in np.arange(0.1, 1.0, 0.1):
#     ror = get_ror(k)
#     print("%.1f %f" % (k, ror))

def create_market_orders(ticker, coin, amount):
    while True:
        try:
            now = datetime.now()
            start_time = get_start_time(ticker)
            end_time = start_time + timedelta(days=1)

            if start_time < now < end_time - timedelta(seconds=10):
                target_price = get_target_price(ticker, 0.5)
                ma15 = get_ma15(ticker)
                current_price = get_current_price(ticker)
                if target_price < current_price:
                    usdt = get_balance("USDT")
                    if usdt > 100:
                        binance.create_market_buy_order(ticker, amount)
                else:
                    coinPrice = get_balance(coin)
                    if coinPrice > 0.9:
                        binance.create_market_sell_order(ticker, coinPrice * 0.99)
                    break
            else:
                coinPrice = get_balance(coin)
                if coinPrice > 0.9:
                    binance.create_market_sell_order(ticker, coinPrice * 0.99)
            time.sleep(1)
        except Exception as e:
            print(e)
            time.sleep(1)

def print_results(ticker):
    print(ticker)
    print("current_price:", get_current_price(ticker))
    print("target_price :", get_target_price(ticker, 0.5))
    print("ma15         :", get_ma15(ticker))

coins = {
    "ATM": 1,
    "DOGE": 1,
    "BTC": 0.001,
    "ADA": 1,
    "MATIC": 1,
    "ETH": 0.01,
    "SHIB": 1000000,
    "SUSHI": 1,
    "AAVE": 0.1,
    "FIS": 1
}

print("Start auto trading!")
#print("balance      :", get_balance("USDT"))

for coin in coins:
    amount = coins[coin]
    ticker = coin + "/USDT"
    #print_results(ticker)
    create_market_orders(ticker, coin, amount)
