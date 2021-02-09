from stocks import *
from api_keys import *
import websocket,json

BASE_URL = 'wss://data.alpaca.markets/stream'
streams = []
ws = None

# Functions for making a socket
def on_open(ws):
    print('Opened websocket')
    auth_data = {
        'action':'authenticate',
        'data':{"key_id": API_KEY, "secret_key": API_SECRET_KEY}
    }
    ws.send(json.dumps(auth_data))

def on_message(ws,message):
    message = json.loads(message)
    if message['stream'] == 'authorization' and message['data']['status'] == 'authorized':
        Stocks = getStockObjs()
        # start streaming minute bars
        for Stock in Stocks:
            if Stock in Stocks[0:5]:
                newStream(ws,Stock,'Q')
            newStream(ws,Stock,'AM')
    stock = getStockObjs(message['T'])
    df = stock.min_data
    if message['ev'] == 'AM':
        stock.addData('minBars',[message['op'],message['h'],message['l'],message['c'],message['v'],message['e']/1000])
    if message['ev'] == 'T':
        stock.addData('trades',[message['p'],message['s']])
    if message['ev'] == 'Q':
        stock.addData('quotes',[message['p'],message['P']])
    
def on_error(ws,error):
    print('Recieved an error: ',error)

def on_close(ws):
    print('Closing Socket')

def newSocket():
    global ws
    ws = websocket.WebSocketApp(BASE_URL,on_open=on_open,on_close=on_close,on_error=on_error,on_message=on_message)
    ws.run_forever()

def getSocket():
    return ws

# Functions for modifying the active socket
def newStream(ws,channel,type):
    # types include trads(T) quotes(Q) or minute bars(AM)
    streams.append(f'{type}.{channel}')
    listen_data = {
    "action": "listen",
    "data": {"streams": streams}
    }
    ws.send(json.dumps(listen_data))
    return streams

def removeStream(ws,channels):
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

def closeSocket(ws):
    ws.close()