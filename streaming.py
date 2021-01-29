import websocket,json
from api_keys import *
from trade import response

BASE_URL = 'wss://data.alpaca.markets/stream'
if response == 'live':
    API_KEY = LIVE_API_KEY
    API_SECRET_KEY = LIVE_API_SECRET_KEY
else:
    API_KEY = PAPER_API_KEY
    API_SECRET_KEY = PAPER_API_SECRET_KEY
streams = []

# Functions for making a socket
def on_open(ws):
    print('Opened websocket')
    auth_data = {
        'action':'authenticate',
        'data':{"key_id": API_KEY, "secret_key": API_SECRET_KEY}
    }
    ws.send(json.dumps(auth_data))

def on_message(message):
    print('Recieved a mesage: ',message)
    if message['stream'] == 'listening':
        streams = message['data']['streams']

def on_error(error):
    print('Recieved an error: ',error)

def on_close(ws):
    print('Closing Socket')

def newSocket():
    ws = websocket.WebSocketApp(BASE_URL,on_open=on_open,on_close=on_close,on_error=on_error,on_message=on_message,)
    ws.run_forever()
    return ws

# Functions for modifying the active socket
def newStream(ws,channels):
    for channel in channels:
        streams.append(channel)
    listen_data = {
    "action": "listen",
    "data": {"streams": streams}
    }
    ws.send(json.dumps(listen_data))

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
