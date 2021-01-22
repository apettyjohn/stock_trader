from functions import *
from datetime import datetime

startup()
logTrade(datetime.timestamp(datetime.now()),'AAPL',105.45,110.0)
lists = ['gainers','losers','most-active','trending-tickers','cryptocurrencies']
#for category in lists:
#   webScrap_list(category)
updateBalance('day trader',0)
print(f'The balance of day trader account is {checkBalance("day trader")}')
