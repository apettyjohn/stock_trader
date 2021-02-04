import sys,threading
from config import *
from alpaca import *
from stream import *
import matplotlib.pyplot as plot

stremas = []

def wait2Market():
    while True:
        open = getClock()['is_open']
        if open:
            print('Market is open')
            return
        else:
            print('Market is closed')
            wait()

# Check account status and balance
account = checkAccount()
if account['status'] != 'ACTIVE':
    print(f'Check account status: {account["status"]}')
    sys.exit()
elif float(account['portfolio_value']) <= 0:
    print('Account balance too low to trade')
    sys.exit()

pullSymbols()
sort_stocks()
minData = minObjs()
#wait2Market()
t1 = threading.Thread(target=newSocket)
t1.start()
time.sleep(1)
print('passed thread')
ws = getSocket()
# for stock in minData[0:2]:
#     print(stock.ticker)
#     streams = newStream(ws,stock.ticker)
# print(streams)
