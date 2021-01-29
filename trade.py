from config import *
from alpaca import *
from streaming import *

ask = input('Paper or live trading: ')
response = ask
account = checkAccount()
print(f'Account status: {account["status"]}')
open = marketOpen()
if open:
    print('Market is open')
    ipos = pullIPOs()
    print(f'There are {ipos[0]} new IPOs today')
else:
    #wait()
    pass
# print(getHistoricalData('AAPL','day',5))