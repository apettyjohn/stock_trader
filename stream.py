from stocks import *
from api_keys import *
from api import *
import numpy as np
import pandas as pd
import websocket,json,time

BASE_URL = 'wss://data.alpaca.markets/stream'
streams = []
ws = None
authorized = False
percentOfPeak = 0.02
stocks_2_trade = 1
balance = 100
trade_size = balance/(stocks_2_trade * 2)

def checkIfAuthorized():
    return authorized

# Functions for making a socket
def on_open(ws):
    auth_data = {
        'action':'authenticate',
        'data':{"key_id": API_KEY, "secret_key": API_SECRET_KEY}
    }
    {"action": "authenticate","data": {"key_id": 'PK6NEE6EQE5R46EVXMZ7', "secret_key": 'xEA3UcGcfe2Y7vYsSwnAVKUraJkTP0aFfHXhPXe7'}}
    ws.send(json.dumps(auth_data))
    print('Opened websocket')

def on_message(ws,message):
    def trade(object):
        global balance
        global n
        stock = getStockObjs(object['T'])
        num = object['P']
        if stock.last == 0:
            stock.last = object['p']
        change = num - stock.last
        # Buying in the trough and selling at the peak
        if stock.direction > 0:
            if np.sign(stock.direction) == np.sign(change):
                if num > stock.peak:
                    stock.peak = num
            else:
                if num < stock.peak:
                    stock.direction = -1
                    stock.trough = num
                    balance += num - stock.buyPrice
                    try:
                        df = pd.read_csv(f'stock_objs/{stock.ticker}/sellPrices.csv')
                        df = df.append(pd.Series([stock.buyIndex,stock.quoteNum,stock.buyPrice,num,balance],index=df.columns),ignore_index=True)
                    except:
                        df = pd.DataFrame([[stock.buyIndex,stock.quoteNum,stock.buyPrice,num,balance]],columns=['index1','index2','buy','sell','balance'])
                    df.to_csv(f'stock_objs/{stock.ticker}/sellPrices.csv',index=False)
        elif stock.direction < 0:
            if np.sign(stock.direction) == np.sign(change):
                    if num < stock.trough:
                        stock.trough = num
            else:
                if num > stock.trough:
                    stock.direction = 1
                    stock.peak = num
                    stock.buyPrice = num
                    stock.buyIndex = stock.quoteNum
        stock.last = num

    message = json.loads(message)
    print(message)
    if message['stream'] == 'authorization' and message['data']['status'] == 'authorized':
        global authorized
        authorized = True
        print('Authenticated')
    message = message['data']
    if message['ev'] == 'Q':
        stock = getStockObjs(message['T'])
        stock.addData(message['P'])
        trade(message)

def newSocket():
    global ws
    ws = websocket.WebSocketApp(BASE_URL,on_open=on_open,on_message=on_message,on_close=lambda ws:print('Closing Socket'),on_error=lambda ws,error:print('Recieved an error: ',error))
    ws.run_forever()

# Functions for modifying the active socket
def newStream(channel,type=''):
    # types include trads(T) quotes(Q) or minute bars(AM)
    streams.append(f'{type}{channel}')
    listen_data = {
    "action": "listen",
    "data": {"streams": streams}
    }
    ws.send(json.dumps(listen_data))
    return streams

def removeStream(channels):
    for channel in channels:
        if channels in streams:
            streams.remove(channel)
        else:
            print(f'Could not remove {channels}, it was not in streams')
    listen_data = {
    "action": "listen",
    "data": {"streams": [streams]}
    }
    ws.send(json.dumps(listen_data))

def closeSocket():
    ws.close()
