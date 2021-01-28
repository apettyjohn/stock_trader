from functions import *
import time

account,response = startup()
print(f'Acount status: {account.status}, balance: {account.equity}')
open = marketOpen()
if open:
    print('Market is open')
    ipos = pullIPOs()
    print(f'There are {ipos[0]} new IPOs today')
else:
    #wait()
    pass
losers = webScrap_list('losers')
print(getHistoricalData('AAPL','day',5))