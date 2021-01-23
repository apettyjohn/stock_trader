from functions import *
from datetime import datetime

startup()
logTrade(datetime.timestamp(datetime.now()),'AAPL',105.45,110.0)
lists = ['gainers','losers','most-active','trending-tickers','cryptocurrencies']
#for category in lists:
#   webScrap_list(category)
updateBalance('day trader',0)
print(f'The balance of day trader account is {checkBalance("day trader")}')

getHistoricalData('AAPL','1d',3)
txt2csv('symbol_lists/nasdaqlisted','|','ndaqSymbols')
