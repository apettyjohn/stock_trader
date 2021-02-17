from logging import error
from stocks import *
from api_keys import *
from api import *
import numpy as np
import pandas as pd
import websocket,json,math

BASE_URL = 'wss://data.alpaca.markets/stream'
streams = []
ws = None
authorized = False
percentOfPeak = 0.02
stocks_2_trade = 5
trade_size = float(checkAccount()['portfolio_value'])/(stocks_2_trade * 2)
balance = 100
df = pd.DataFrame([['-','-','-',balance]],columns=['stock','buy','sell','balance'])
df.to_csv('tradeLog.csv',index=False)


def checkIfAuthorized():
    global authorized
    return authorized

# Functions for making a socket
def on_open(ws):
    auth_data = {
        'action':'authenticate',
        'data':{"key_id": API_KEY, "secret_key": API_SECRET_KEY}
    }
    ws.send(json.dumps(auth_data))
    print('Opened websocket')

def on_message(message):
    message = json.loads(message)
    print(message)
    if message['stream'] == 'authorization' and message['data']['status'] == 'authorized':
        global authorized
        authorized = True
        print('Authenticated')
    message = message['data']
    stock = getStockObjs(message['T'])
    if message['ev'] == 'Q':
        stock.last = float(message['P'])
        change = float(message['P']) - stock.last
        if stock.direction == 0:
            stock.direction = -1
        # Buying in the trough and selling at the peak
        if stock.direction > 0:
            if np.sign(stock.direction) == np.sign(change):
                if float(message['P']) > stock.peak:
                    stock.peak = float(message['P'])
                    print(f'New peak for {stock.ticker}')
            else:
                if abs(float(message['P']) - stock.peak) < percentOfPeak * stock.buyPrice:
                    pass
                else:
                    stock.direction = -1
                    print(f'Direction changed to -1 for {stock.ticker}')
                    stock.trough = float(message['p'])
                    global balance
                    global df
                    balance += message['P'] - stock.buyPrice
                    df.append(pd.Series([stock.ticker,stock.buyPrice,message['P'],balance],index=df.columns),ignore_index=True)
                    df.to_csv('tradeLog.csv')
                    print(f'New sell order for {stock.ticker}')
        elif stock.direction < 0:
            if np.sign(stock.direction) == np.sign(change):
                    if float(message['p']) < stock.trough:
                        stock.trough = float(message['p'])
                        print(f'New trough for {stock.ticker}')
            else:
                if abs(float(message['p']) - stock.trough) > percentOfPeak * stock.trough:
                    stock.direction = 1
                    print(f'Direction changed to 1 for {stock.ticker}')
                    stock.peak = float(message['P'])
                    stock.buyPrice = float(message['p'])
                    print(f'New buy order for {stock.ticker}')
                else:
                    pass

def newSocket():
    global ws
    ws = websocket.WebSocketApp(BASE_URL,on_open=on_open,on_message=on_message,on_close=lambda:print('Closing Socket'),on_error=lambda error:print('Recieved an error: ',error))
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