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

pullSymbols()
sort_stocks()

# Wait until market is open
#wait2Market()
