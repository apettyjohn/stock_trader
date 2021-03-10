import stopwatch
from stocks import *
from api_keys import *
from api import *
import numpy as np
import pandas as pd
import websocket,json
from scipy.ndimage.filters import gaussian_filter1d
from stopwatch import Stopwatch

BASE_URL = 'wss://data.alpaca.markets/stream'
streams = []
ws = None
authorized = False
percentOfPeak = 0.02
stocks_2_trade = 1
balance = 100
state = 'sell'
trade_size = 5
stpwtch = Stopwatch()
stpwtch.start()

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
    def paperTrade(num,stock):
        def trade(num,n,trade):
            global state
            if trade == 'sell' or trade == 'buy':
                try:
                    df1 = pd.read_csv(f'stock_objs/{stock.ticker}/sellPrices.csv')
                    df1 = df1.append(pd.Series([n,num,trade],index=df1.columns),ignore_index=True)
                except:
                    df1 = pd.DataFrame([[n,num,trade]],columns=['index','change','type'])
                df1.to_csv(f'stock_objs/{stock.ticker}/sellPrices.csv',index=False)
                state = trade
        if stpwtch.duration > 0.2:
            stpwtch.restart()
            try:
                last = stock.quotes['price'][stock.quotes.index[-1]]
                if last != num:
                    stock.addData(num)
                    n = stock.n
                    if len(stock.quotes.index) > 10:
                        y_smooth1 = gaussian_filter1d(stock.quotes['price'][-9:], 2)
                    else:
                        y_smooth1 = gaussian_filter1d(stock.quotes['price'], 2)
                    stock.y_smooth.append(y_smooth1[-1])
                    stock.n += 1
                    if n < 1:
                        return
                    elif n < 2:
                        stock.y_deriv1.append(stock.y_smooth[-1]-stock.y_smooth[-2])
                        return
                    stock.y_deriv1.append(stock.y_smooth[-1]-stock.y_smooth[-2])
                    stock.y_deriv2.append(stock.y_deriv1[-1]-stock.y_deriv1[-2])
                    if state == 'sell':
                        if np.sign(stock.y_deriv1[-1]) + np.sign(stock.y_deriv1[-2]) == 0:
                            if np.sign(stock.y_deriv2[-1]) < 0:
                                trade(num,n,'buy')
                    else:
                        if np.sign(stock.y_deriv1[-1])+np.sign(stock.y_deriv1[-2]) == 0:
                            if np.sign(stock.y_deriv2[-1]) > 0:
                                trade(num,n,'sell')
            except:
                stock.addData(num)
                y_smooth1 = gaussian_filter1d(stock.quotes['price'], 2)
                stock.y_smooth.append(y_smooth1[-1])
                stock.n += 1

    def liveTrade(num,stock):
        def trade(trade):
            global state
            state = trade
            if trade == 'buy':
                td_newOrder(stock.ticker,trade_size,'buy')
            elif trade == 'sell':
                td_newOrder(stock.ticker,trade_size,'sell')
    
        if stpwtch.duration > 0.5:
            try:
                last = stock.quotes['price'][stock.quotes.index[-1]]
                if last != num:
                    stock.addData(num)
                    n = stock.n
                    if len(stock.quotes.index) > 10:
                        y_smooth1 = gaussian_filter1d(stock.quotes['price'][-9:], 2)
                    else:
                        y_smooth1 = gaussian_filter1d(stock.quotes['price'], 2)
                    stock.y_smooth.append(y_smooth1[-1])
                    stock.n += 1
                    if n < 1:
                        return
                    elif n < 2:
                        stock.y_deriv1.append(stock.y_smooth[-1]-stock.y_smooth[-2])
                        return
                    stock.y_deriv1.append(stock.y_smooth[-1]-stock.y_smooth[-2])
                    stock.y_deriv2.append(stock.y_deriv1[-1]-stock.y_deriv1[-2])
                    global state
                    if state == 'sell':
                        if np.sign(stock.y_deriv1[-1]) + np.sign(stock.y_deriv1[-2]) == 0:
                            if np.sign(stock.y_deriv2[-1]) < 0:
                                trade('buy')
                                stock.orderFilled = False
                                orders = []
                                stpwtch.restart()
                                while not(stock.orderFilled):
                                    filled_orders = td_getOrder(status='filled')
                                    for order in filled_orders:
                                        if order['orderLegCollection'][0]['instrument']['symbol'] == stock.ticker:
                                            orders.append(order)
                                    if orders[0]['orderLegCollection'][0]['instruction'] == 'BUY':
                                        stock.orderFilled = True
                                    if stpwtch.duration > 3:
                                        state = 'sell'
                                        break
                    else:
                        if np.sign(stock.y_deriv1[-1])+np.sign(stock.y_deriv1[-2]) == 0:
                            if np.sign(stock.y_deriv2[-1]) > 0:
                                trade('sell')
                                stock.orderFilled = False
                                orders = []
                                stpwtch.restart()
                                while not(stock.orderFilled):
                                    filled_orders = td_getOrder(status='filled')
                                    for order in filled_orders:
                                        if order['orderLegCollection'][0]['instrument']['symbol'] == stock.ticker:
                                            orders.append(order)
                                    if orders[0]['orderLegCollection'][0]['instruction'] == 'SELL':
                                        stock.orderFilled = True
                                    if stpwtch.duration > 3:
                                        state = 'buy'
                                        break
            except:
                stock.addData(num)
                y_smooth1 = gaussian_filter1d(stock.quotes['price'], 2)
                stock.y_smooth.append(y_smooth1[-1])
                stock.n += 1
            stpwtch.restart()

    message = json.loads(message)
    if message['stream'] == 'authorization' and message['data']['status'] == 'authorized':
        global authorized
        authorized = True
        print('Authenticated')
    message = message['data']
    if message['ev'] == 'Q':
        stock = getStockObjs(message['T'])
        #paperTrade(message['P'],stock)
        liveTrade(message['P'],stock)

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
    print(f'Now listening to {channel}')
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
