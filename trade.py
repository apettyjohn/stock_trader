import sys,threading
from pynput import keyboard
from config import *
from stream import *

def keyboardListener():
    def on_press(key):
        if key == keyboard.Key.esc:
            global done
            done = True
            print('Closing Keyboard Listener')
            closeSocket()
            return False
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
def accountCheck():
    # Check account status and balance
    account = checkAccount()
    if account['status'] != 'ACTIVE':
        print(f'Check account status: {account["status"]}')
        sys.exit()
    elif float(account['portfolio_value']) <= 0:
        print('Account balance too low to trade')
        sys.exit()
    return account
def startStream():
    # starting websocket and keyboard listener thread
    t1 = threading.Thread(target=newSocket)
    t1.start()
    # wait until websocket connects
    while not(checkIfAuthorized()):
        time.sleep(1)
    # start listening to stock quotes
    tickers = os.listdir('stock_objs')
    for ticker in tickers:
        newStream(ticker,'Q.')

done = False
stocks_2_trade = 1
accountCheck()

while True:
    #pullSymbols(max_price=5)
    save_stocks(stocks_2_trade)
    create_stock_objs()
    keyboardListener()
    startStream()
    # do this code until user quits or day is over
    while not(done):
        time.sleep(0.5)
    closeSocket()
    break

stocks = getStockObjs()
for stock in stocks:
    stock.plot()
