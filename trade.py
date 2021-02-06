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

#pullSymbols()
sort_stocks()
stock = StockObjs()[0]
stock.plot()
# t2 = threading.Thread(target=lambda: stocks.plot(stocks.minData,stocks.ticker)) 
# t2.start()
# wait2Market()
# t1 = threading.Thread(target=newSocket)
# t1.start()
# time.sleep(2)
# ws = getSocket()
# time.sleep(5)
# closeSocket(ws)
# for stock in minData[0:2]:
#     print(stock.ticker)
#     streams = newStream(ws,stock.ticker)
# print(streams)
