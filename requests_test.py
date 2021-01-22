from lxml import html
import requests as requests
import pandas as pd

print('This program will look for stocks in lists of \n gainers,losers,most-active,trending-tickers, and cryptocurrencies')
type = input('What type of stocks are you looking for? ')
response = requests.get(f'https://finance.yahoo.com/{type}')
if response.status_code == 200:
        print('Successfully pulled list')
else:
    print(f'Http request failed. Status code: {response.status_code}')

tree = html.fromstring(response.content)
symbols = tree.xpath('//*[@id="scr-res-table"]/div[1]/table/tbody/tr/td[1]/a/text()')
full_name = tree.xpath('//*[@id="scr-res-table"]/div[1]/table/tbody/tr/td[2]/text()')
price = tree.xpath('//*[@id="scr-res-table"]/div[1]/table/tbody/tr/td[3]/span/text()')
change = tree.xpath('//*[@id="scr-res-table"]/div[1]/table/tbody/tr/td[4]/span/text()')
percent_change = tree.xpath('//*[@id="scr-res-table"]/div[1]/table/tbody/tr/td[5]/span/text()')
volume = tree.xpath('//*[@id="scr-res-table"]/div[1]/table/tbody/tr/td[6]/span/text()')
mkt_cap = tree.xpath('//*[@id="scr-res-table"]/div[1]/table/tbody/tr/td[8]/span/text()')

my_columns = ['Symbols','Full Name','Price','Change','% Change','Volume','Market Cap']
fields = [symbols,full_name,price,change,percent_change,volume,mkt_cap]
data = list(range(len(fields)))
for n in list(range(len(symbols))):
    for i in list(range(len(fields))):
        print(f'{n},{i}')
        field = fields[i]
        data[i] = field[n]
    try:
        df = df.append(pd.Series(data,index=my_columns),ignore_index=True)
    except:
        df = pd.DataFrame([data],columns=my_columns)

df.to_csv(f'{type}.csv',index=False)