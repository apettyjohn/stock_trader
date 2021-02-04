from config import *
from alpaca import *
from streaming import *
import sys
import matplotlib.pyplot as plot

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

#pullSymbols()
sort_stocks()
minData = minObjs()[10]
line = minData.df
minData.df.index = range(minData.timeframe)
line.plot.line(title=f'Minute data for {minData.ticker}',y='close')
plot.show(block=True)
#wait2Market()
