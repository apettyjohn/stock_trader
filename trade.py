import sys,threading
from pynput import keyboard
from config import *
from stream import *

def on_release(key):
    if key == keyboard.Key.esc:
        global done
        done = True
        print('Quitting keyboard listener')
        listener.stop()
        #closeSocket()
def accountCheck():
    # Check account status and balance
    account = checkAccount()
    if account['status'] != 'ACTIVE':
        print(f'Check account status: {account["status"]}')
        sys.exit()
    elif float(account['portfolio_value']) <= 0:
        print('Account balance too low to trade')
        sys.exit()
def startStream():
    # starting websocket and keyboard listener thread
    t1 = threading.Thread(target=newSocket)
    t1.start()
    # wait until websocket connects
    while not(checkIfAuthorized()):
        time.sleep(1)
    print('Passed Authorization waiting period')
    # start listening to stock quotes
    tickers = os.listdir('stock_objs')
    for ticker in tickers:
        newStream(ticker,'Q.')

done = False
accountCheck()

while True:
    #pullSymbols(max_price=5)
    save_stocks(stocks_2_trade)
    create_stock_objs()
    #startStream()
    listener = keyboard.Listener(on_release=on_release)
    listener.start()
    # do this code until user quits or day is over
    while not(done):
        time.sleep(0.25)
    break
