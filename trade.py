import math,json,time,os
import pandas as pd
from api_keys import *
from scipy.ndimage.filters import gaussian_filter1d
import numpy as np
import matplotlib.pyplot as plt
from pynput import keyboard
from stopwatch import Stopwatch
import robin_stocks.robinhood as rh

def keyboardListener():
    def on_press(key):
        if key == keyboard.Key.esc:
            global done
            done = True
            print('Closing Keyboard Listener')
            rh_logout()
            return False
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
def trade(trade):
    global state
    global trades
    global buyPrice
    global positionQty
    global trades
    global balance
    state = trade
    num = rh_getPrice(crypto)    
    ask = round(float(num['ask_price']),roundTo)
    bid = round(float(num['bid_price']),roundTo)
    if trade == 'buy':
        num = ask
        if crypto != 'DOGE':
            if roundTo > 2:
                num = round(num,2)
        trade_size = math.floor(balance/(2*num))
        positionQty = trade_size
        rh_marketOrder(crypto,trade_size,'buy')
        time.sleep(0.5)
        while True:
            order = rh.orders.get_all_crypto_orders()[0]
            if order['state'] != 'confirmed' and order['state'] != 'unconfirmed':
                break
        buyPrice = float(order['rounded_executed_notional'])
        if not(suppressOutput):
            print(f'Bought {trade_size} shares of {crypto} @ {buyPrice}')
    elif trade == 'sell':
        num = bid
        rh_marketOrder(crypto,positionQty,'sell')
        time.sleep(0.5)
        while True:
            order = rh.orders.get_all_crypto_orders()[0]
            if order['state'] != 'confirmed' and order['state'] != 'unconfirmed':
                break
        if not(suppressOutput):
            print(f'Sold {positionQty} shares of {crypto} @ {num}')
        if buyPrice == 0:
            buyPrice = bid
        balance += (num-buyPrice)*positionQty
        positionQty = 0
    try:
        df2 = pd.read_csv(f'stock_objs/{crypto}/trades.csv')
        df2 = df2.append(pd.Series([df.index[-1],num,trade,round(balance,roundTo)],index=df2.columns),ignore_index=True)
    except:
        df2 = pd.DataFrame([[df.index[-1],num,trade,round(balance,roundTo)]],columns=['index','price','side','balance'])
    df2.to_csv(f'stock_objs/{crypto}/trades.csv',index=False)
    trades += 1
def compareDateStrings(str1,str2):
    # expected format '2021-03-02T13:03:08.089111' 
    def str2int(string):
        date = string[:10].replace('-','')
        timestamp = string[11:].replace(':','')
        string = float(date+timestamp)
        return string
    str1 = str2int(str1)
    str2 = str2int(str2)
    return str1 > str2
def plot(df1,df2):
    def regressions(x1,y1):
        y_smooth1 = gaussian_filter1d(y1, 3)
        y_deriv1 = gaussian_filter1d(y_smooth1,2,order=1)
        y_deriv2 = gaussian_filter1d(y_smooth1,2,order=2)
        fig, ax = plt.subplots(3)
        fig.suptitle("Graph")
        ax[0].plot(x1,y1,c='black',linewidth=1.0)
        ax[0].scatter(x1,y_smooth1,c='red',s=15)
        ax[1].scatter(x1,y_deriv1,c='blue',s=15)
        ax[2].scatter(x1,y_deriv2,c='blue',s=15)
        ax[0].grid()
        ax[1].grid()
        ax[2].grid()
        plt.show()
    def buySell(x1,y1,x_b,y_b,x_s,y_s):
        fig,ax = plt.subplots(3)
        ax[0].plot(y1,c='black',linewidth=1.0)
        ax[0].plot(y_smoothAsk,c='blue',linewidth=2.0)
        ax[0].scatter(x_b,y_b,s=20,c='green') # buy
        ax[0].scatter(x_s,y_s,s=20,c='red') # sell
        ax[1].plot(y_deriv1Ask)
        ax[2].plot(y_deriv2Ask)
        ax[0].grid()
        ax[1].grid()
        ax[2].grid()
        plt.show()

    x1 = np.array(range(len(df1.index)))
    y1 = []
    for x in df1['mark']:
        y1.append(x)
    x2 = []
    y2 = []
    x3 = []
    y3 = []
    for x in range(len(df2.index)):
        if df2['side'][x] == 'buy':
            x2.append(df2['index'][x])
            y2.append(df2['price'][x])
        else:
            x3.append(df2['index'][x])
            y3.append(df2['price'][x])
    buySell(x1,y1,x2,y2,x3,y3)
    #regressions(x1,y1)
# Robinhood
def rh_login():
    try:
        rh.login(username=rh_username,password=rh_password,expiresIn=86400,by_sms=True)
        print('Authenticated Robinhood API')
    except Exception as e:
        print("Error logging in:", e)
def rh_logout(signBackIn=False):
    try:
        rh.logout()
        print('Logged out of robinhood api')
        time.sleep(0.1)
    except Exception as e:
        print("Error logging out:", e)

    if signBackIn:
        rh_login()
def rh_getPrice(crypto):
    try:
        return rh.crypto.get_crypto_quote(crypto)
    except Exception as e:
        print("Error getting stock price:", e)
def rh_marketOrder(symbol,shares,instruction):
    try:
        if instruction == 'buy':
            r = rh.order_buy_crypto_by_quantity(symbol,shares,jsonify=False) 
        elif instruction == 'sell':
            r = rh.order_sell_crypto_by_quantity(symbol,shares,jsonify=False)
        print(f'Order placed to {instruction} {shares} of {symbol}') 
    except Exception as e:
        print("Error placing market order:", e)
    return json.loads(r.content)
def rh_limitOrder(symbol,shares,ammountInDollars,instruction):
    try:
        if instruction == 'buy':
            r = rh.order_buy_crypto_limit(symbol,float(shares),float(ammountInDollars),jsonify=False)
        elif instruction == 'sell':
            r = rh.order_sell_crypto_limit(symbol,float(shares),float(ammountInDollars),jsonify=False)
    except Exception as e:
                print("Error placing limit order:", e)
    return json.loads(r.content)
def rh_getHistoricalCryptoPrice(stock,interval='5minute',span='day'):
    # Valid intervals: ['15second', '5minute', '10minute', 'hour', 'day', 'week']
    # Valid time spans: ['hour', 'day', 'week', 'month', '3month', 'year', '5year']
    try:
        data = rh.crypto.get_crypto_historicals(stock, interval=interval, span=span)
        return data
    except Exception as e:
        print("Error getting historical data:", e)
def save_stock(name):
    print(f'Saving stock {name}')
    # clean stock directory
    try:
        stock_objs = os.listdir('stock_objs')
        if name in stock_objs:
            files = os.listdir(f'stock_objs/{name}')
            for file in files:
                os.remove(f'stock_objs/{name}/{file}')
            os.rmdir(f'stock_objs/{name}')
    except:
        pass
    os.mkdir(f'stock_objs/{name}')
def trend(crypto,fractionOfDay=1,interval='5minute',span='day'):
    data = rh_getHistoricalCryptoPrice(crypto,interval=interval,span=span)
    prices = []
    for num in data[-math.ceil(len(data)*fractionOfDay):]:
        prices.append((float(num['close_price'])+float(num['open_price']))/2)
    diffs = np.diff(prices)
    return round(sum(diffs),5)

# Setup
y_smoothBid = []
y_smoothAsk = []
y_deriv1Bid = []
y_deriv1Ask = []
y_deriv2Bid = []
y_deriv2Ask = []
done = False
suppressOutput = False
dropQuotes = False
trades = 0
buyPrice = 0
positionQty = 0
roundTo = 3
crypto = 'ETC'
state = 'sell'
stpwtch = Stopwatch()
totalTime = Stopwatch()
time2Logout = Stopwatch()
stpwtch.start()
totalTime.start()
time2Logout.start()
keyboardListener()
rh_login()
save_stock(crypto)
print(f'Trading {crypto}')
# ------------------------
balance = float(rh.account.load_account_profile()['crypto_buying_power'])
starting_balance = balance
max_order_size = float(rh.crypto.get_crypto_info(crypto)['max_order_size'])
num = rh_getPrice(crypto)
ask = round(float(num['ask_price']),roundTo)
bid = round(float(num['bid_price']),roundTo)
df = pd.DataFrame([[ask,bid,(ask+bid)/2]],columns=['ask','bid','mark'])
df.to_csv(f'stock_objs/{crypto}/quotes.csv',index=False)
y_smoothAsk.append(ask)
y_smoothBid.append(bid)
# do this code until user quits
while not(done):
    if time2Logout.duration > 86000:
        rh_logout(signBackIn=True)
    try:
        num = rh_getPrice(crypto)
        ask = round(float(num['ask_price']),roundTo)
        bid = round(float(num['bid_price']),roundTo)
        if state == 'buy': # I'm really selling here
            num = bid
            column = 'bid'
        elif state == 'sell': # This actually means buy
            num = ask
            column = 'ask'
        last = df[column].iat[-1]
        if last != num:
            df = df.append(pd.Series([ask,bid,(ask+bid)/2],index=df.columns),ignore_index=True)
            df.to_csv(f'stock_objs/{crypto}/quotes.csv',index=False)
            if len(df.index) > 20:
                y_smoothAsk.append(gaussian_filter1d(df['ask'][-19:], 3)[-1])
                y_smoothBid.append(gaussian_filter1d(df['bid'][-19:], 3)[-1])
                if dropQuotes:
                    if len(df.index) > 1000:
                        df.drop(index=0,inplace=True)
                        df.reset_index(drop=True)
                        y_smoothBid.remove(y_smoothBid[0])
                        y_smoothAsk.remove(y_smoothAsk[0])
                        y_deriv1Bid.remove(y_deriv1Bid[0])
                        y_deriv1Ask.remove(y_deriv1Ask[0])
                        y_deriv2Bid.remove(y_deriv2Bid[0])
                        y_deriv2Ask.remove(y_deriv2Ask[0])
            else:
                y_smoothAsk.append(gaussian_filter1d(df['ask'], 3)[-1])
                y_smoothBid.append(gaussian_filter1d(df['bid'], 3)[-1])
            if len(y_deriv1Ask) < 5:
                y_deriv1Ask.append(y_smoothAsk[-1]-y_smoothAsk[-2])
                y_deriv1Bid.append(y_smoothBid[-1]-y_smoothBid[-2])
                continue
            else:
                y_deriv1Ask.append(gaussian_filter1d(np.diff(y_smoothAsk), 3)[-1])
                y_deriv1Bid.append(gaussian_filter1d(np.diff(y_smoothBid), 3)[-1])
            if len(y_deriv2Ask) < 5:
                y_deriv2Ask.append(y_deriv1Ask[-1]-y_deriv1Ask[-2])
                y_deriv2Bid.append(y_deriv1Bid[-1]-y_deriv1Bid[-2])
                continue
            else:
                y_deriv2Ask.append(gaussian_filter1d(np.diff(y_deriv1Ask), 3)[-1])
                y_deriv2Bid.append(gaussian_filter1d(np.diff(y_deriv1Bid), 3)[-1])
            if stpwtch.duration > 0.1:
                orderState = rh.orders.get_all_crypto_orders()[0]['state']
                if orderState != 'confirmed' and orderState != 'unconfirmed':
                    if state == 'sell':
                        minTrend = trend(crypto,0.01)
                        secTrend = trend(crypto,0.01,interval='15second',span='hour')
                        if minTrend > 0 and secTrend > 0:
                            if np.sign(y_deriv2Ask[-1]) + np.sign(y_deriv2Ask[-2]) == 0:
                                if y_deriv1Ask[-1] > y_deriv1Ask[-5]:
                                    trade('buy')
                    else:
                        if np.sign(y_deriv2Bid[-1])+np.sign(y_deriv2Bid[-2]) == 0:
                            if y_deriv1Bid[-1] < y_deriv1Bid[-5]:
                                if round(num,roundTo) > round(buyPrice,roundTo):
                                    trade('sell')
                        elif round(buyPrice,roundTo)-round(num,roundTo) > round(buyPrice,roundTo)*0.01:
                            trade('sell')
                    stpwtch.restart()
    except Exception as e:
        print(f'Encountered exception:',type(e).__name__,e)
        break

try:
    if not(suppressOutput):
        print(f'Made {trades} trades')
    print(f'Program ran for {round(totalTime.duration,2)} seconds')
    df2 = pd.read_csv(f'stock_objs/{crypto}/trades.csv')
    print(f'Final balance: {df2["balance"].iat[-1]}, Profit: {100*(round(df2["balance"].iat[-1]-starting_balance,roundTo)/df2["balance"].iat[-1])}%')
    plot(df,df2) # df = quotes, df2 = trades
except Exception as e:
    print(f'Encountered exception:',type(e).__name__,e)