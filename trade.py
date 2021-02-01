from config import *
from alpaca import *
from streaming import *
import sys,os
import pandas as pd

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

# Wait until market is open
while True:
    #wait2Market()
    ipos = pullIPOs()
    print(f'There are {ipos[0]} new IPOs today')
    # Update historical Data
    # symbols = os.listdir('stock_profiles/historical')
    # if symbols:
    #     for file in os.listdir('stock_profiles/historical/'):
    #         ticker = file[0:-4]
    #         print(getHistoricalData(ticker,'day',50))
    # else:
    #     for ticker in pd.read_csv('ndaqSymbols.csv'):
    #         print(getHistoricalData(ticker,'day',50))
    #     for ticker in pd.read_csv('otherSymbols.csv'):
    #         print(getHistoricalData(ticker,'day',50))
    break
