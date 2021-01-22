import pandas as pd
from datetime import datetime
from lxml import html
import requests

def startup():
    try:
        df = pd.read_csv('balance.csv')
    except:
        print('balance.csv does not exist')
        data = [['day trader',0]]
        df = pd.DataFrame(data, columns=['Account','Balance'])
        df.to_csv('balance.csv', index=False)
        print('Initialized new balance sheet')
    balance_data = df.to_dict()
    dt_funds = balance_data['Balance'][0]
    print(f"Current Balance: ${dt_funds}")

def logTrade(time,ticker,buy,sell):
    my_columns = ['Time','Ticker','Buy','Sell','Net']
    dt = datetime.fromtimestamp(time)
    try:
        df = pd.read_csv('trades.csv')
        df = df.append(pd.Series([dt,ticker,buy,sell,sell-buy],index=my_columns),ignore_index=True)
    except:
        print('trades.csv does not exist')
        file = open('trades.csv',"x")
        df = pd.DataFrame([[dt,ticker,buy,sell,sell-buy]],columns=my_columns)
        print('Initialized new trading record')
    df.to_csv('trades.csv',index=False)

def webScrap_list(type):
    print(f'Making a request for list of stock {type}')
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
            field = fields[i]
            data[i] = field[n]
        try:
            df = df.append(pd.Series(data,index=my_columns),ignore_index=True)
        except:
            df = pd.DataFrame([data],columns=my_columns)

    df.to_csv(f'{type}.csv',index=False)