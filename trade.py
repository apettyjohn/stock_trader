import sys,threading
from config import *
from alpaca import *
from stream import *

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
            return

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
stocks = StockObjs()[5]
stocks.plot(stocks.minData,stocks.ticker) #plots should probably be on a separate thread
wait2Market()
# t1 = threading.Thread(target=newSocket)
# t1.start()
# time.sleep(5)
# print('passed thread')
# ws = getSocket()
# for stock in minData[0:2]:
#     print(stock.ticker)
#     streams = newStream(ws,stock.ticker)
# print(streams)
