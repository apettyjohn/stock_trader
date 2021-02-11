import sys,threading,os,subprocess
from datetime import datetime
from pynput import keyboard
from config import *
from alpaca import *
from stream import *
from stocks import *
from tdAmeritrade import *

streams = []
done = False

def wait2Market():
    while True:
        open = getClock()['is_open']
        if open:
            print('Market is open')
            return
        else:
            print('Market is closed')
            wait()
            return
def on_release(key):
    if key == keyboard.Key.esc:
        print('Quitting keyboard listener')
        global done
        done = True
        listener.stop()

# Check account status and balance
account = checkAccount()
if account['status'] != 'ACTIVE':
    print(f'Check account status: {account["status"]}')
    sys.exit()
elif float(account['portfolio_value']) < 0:
    print('Account balance too low to trade')
    sys.exit()

# completed = subprocess.Popen('node server.js')
# time.sleep(2)

while True:
    #pullSymbols()
    save_stocks()
    create_stock_objs()
    #wait2Market()
    # starting websocket thread
    # t1 = threading.Thread(target=newSocket)
    # t1.start()
    # starting keyboard listener thread
    listener = keyboard.Listener(on_release=on_release)
    listener.start()
#     # do this code until user quits or day is over
#     tic = datetime.now()
    while not(done):
        time.sleep(0.5)
        
    if done:
        # ws = getSocket()
        # closeSocket(ws)
        # completed = subprocess.Popen('taskkill /f /im node.exe')
        # time.sleep(.25)
        break
