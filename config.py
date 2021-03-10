from api import *
from stocks import *
from datetime import datetime
from lxml import html
from tqdm import tqdm 
import pandas as pd
import requests, time, os

# Foundation Functions
def pullSymbols(max_price):
    print('Getting a list of symbols')
    allSymbols = []
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'}
    r = requests.get(f'https://finviz.com/screener.ashx?v=152&f=geo_usa,sh_opt_short,sh_price_u{int(max_price)}&r=0&c=0,1,5,6,49,50,51,52,65,66,67',headers=headers)
    tree = html.fromstring(r.content)
    pages = int(tree.xpath('//*[@id="screener-content"]/table/tr[7]/td/a/text()')[-1])
    # pull data from each page
    for n in tqdm (range(0,pages), desc="Loading..."):
        if n != 1:
            r = requests.get(f'https://finviz.com/screener.ashx?v=152&f=geo_usa,sh_opt_short,sh_price_u{int(max_price)}&r={n*20}&c=0,1,5,6,49,50,51,52,65,66,67',headers=headers)
            tree = html.fromstring(r.content)
        base_xpath = '//*[@id="screener-content"]/table/tr[4]/td/table/tr[{}]/td[{}]/a/{}text()'
        last_page = len(tree.xpath('//*[@id="screener-content"]/table/tr[4]/td/table/tr/td[2]/a/text()'))
        # add the data row by row
        if n == pages-1:
            end = last_page
        else:
            end = 22
        for i in range(2,end):
            try:
                try:
                    prices = tree.xpath(base_xpath.format(i,9,'span/'))[0]
                except:
                    prices = tree.xpath(base_xpath.format(i,9,''))[0]
                try:
                    change = tree.xpath(base_xpath.format(i,10,'span/'))[0]
                except:
                    change = tree.xpath(base_xpath.format(i,10,''))[0]
                symbol = tree.xpath(base_xpath.format(i,2,''))[0]
                volume = tree.xpath(base_xpath.format(i,11,''))[0]
                atr = tree.xpath(base_xpath.format(i,5,''))[0]
                if ',' in volume:
                    volume = float(volume.replace(',',''))
                volatile = tree.xpath(base_xpath.format(i,6,''))[0][0:-1]
                #print(symbol,prices,atr,change,volume)
                row = [symbol,float(prices),float(atr),round(float(volatile),1),float(change[0:-1]),float(volume)]
                # only add data if it's affordable
                if float(prices) < max_price:
                    allSymbols.append(row)
            except:
                pass
    df = pd.DataFrame(allSymbols,columns=['Symbol','Price','ATR','Volatility','% Change','Volume'])
    df.to_csv('allSymbols.csv',index=False)
    print('Successfully saved symbol list')
    print(f'Found {len(allSymbols)} symbols')

def create_stock_objs():
    # Variables
    print('Creating stock objs')
    stocks = os.listdir('stock_objs')
    # creating stock objects
    for i in tqdm(range(len(stocks)), desc="Loading..."):
        addStockObjs(Stock(stocks[i]),'a')
    print('Successfully created stock objects')

def save_stocks(stocks_2_trade):
    print('Saving stocks')
    # clean stock directory
    try:
        stock_objs = os.listdir('stock_objs')
        for folder in stock_objs:
            files = os.listdir(f'stock_objs/{folder}')
            for file in files:
                os.remove(f'stock_objs/{folder}/{file}')
            os.rmdir(f'stock_objs/{folder}')
    except:
        os.mkdir('stock_objs')
    # get symbols
    df1 = pd.read_csv('allSymbols.csv')
    #df1['% Change'] = [abs(elem) for elem in df1['% Change']]
    df1.sort_values(by=['Volume','% Change'],inplace=True,ascending=False)
    # variables
    watchlist_max_length = stocks_2_trade
    # loop through dataframe and save data
    for i in tqdm(range(watchlist_max_length), desc="Loading..."):
        n = df1.index[i]
        symbol = df1['Symbol'][n]
        try:
            os.mkdir(f'stock_objs/{symbol}')
        except:
            # skip repeats
            watchlist_max_length += 1
            continue
        check = True
        while check:
            try:
                min = td_priceHistory(symbol,'day',2,'minute',1)['candles']
                hour = td_priceHistory(symbol,'day',2,'minute',30)['candles']
                check = False
            except:
                time.sleep(3)
        # convert json from response into a dataframe
        data = []
        for n in range(len(min)):
            row = min[n]
            data.append([row['open'],row['high'],row['low'],row['close'],row['volume'],row['datetime']])
        min_data = pd.DataFrame(data,columns=['open','high','low','close','volume','time'])
        data = []
        for n in range(len(hour)):
            row = hour[n]
            data.append([row['open'],row['high'],row['low'],row['close'],row['volume'],row['datetime']])
        hour_data = pd.DataFrame(data,columns=['open','high','low','close','volume','time'])
        # save dataframes into csv files
        with open(f'stock_objs/{symbol}/min_data.csv','w') as f:
            min_data.to_csv(f,index=False)
        with open(f'stock_objs/{symbol}/hour_data.csv','w') as f:
            hour_data.to_csv(f,index=False)

def save_stock(name):
    print(f'Saving stock {name}')
    # clean stock directory
    try:
        stock_objs = os.listdir('stock_objs')
        if name in stock_objs:
            files = os.listdir(f'stock_objs/{name}')
            for file in files:
                os.remove(f'stock_objs/{name}/{file}')
            os.rmdir(f'stock_objs/{name}')
    except:
        pass
    os.mkdir(f'stock_objs/{name}')

# Trading Strategy Functions
def webScrap_list(type):
    # pulls lists of stocks from yahoo 
    print(f'Making a request for list of {type}')
    try:
        response = requests.get(f'https://finance.yahoo.com/{type}')
        if response.status_code == 200:
            print('Successfully pulled list')
        else:
            print(f'No response returned, status code: {response.status_code}')
    except:
        print(f'Http request failed. Check your connection')
        return
    
    # save data into lists
    tree = html.fromstring(response.content)
    symbols = tree.xpath('//*[@id="scr-res-table"]/div[1]/table/tbody/tr/td[1]/a/text()')
    full_name = tree.xpath('//*[@id="scr-res-table"]/div[1]/table/tbody/tr/td[2]/text()')
    price = tree.xpath('//*[@id="scr-res-table"]/div[1]/table/tbody/tr/td[3]/span/text()')
    change = tree.xpath('//*[@id="scr-res-table"]/div[1]/table/tbody/tr/td[4]/span/text()')
    percent_change = tree.xpath('//*[@id="scr-res-table"]/div[1]/table/tbody/tr/td[5]/span/text()')
    volume = tree.xpath('//*[@id="scr-res-table"]/div[1]/table/tbody/tr/td[6]/span/text()')
    mkt_cap = tree.xpath('//*[@id="scr-res-table"]/div[1]/table/tbody/tr/td[8]/span/text()')

    fields = [symbols,full_name,price,change,percent_change,volume,mkt_cap]
    data = list(range(len(fields)))
    array = [type]
    # group data into rows for each stock respecively
    for n in list(range(len(symbols))):
        for i in list(range(len(fields))):
            field = fields[i]
            data[i] = field[n]
            if i == len(fields)-1:
                array.append(data)
    return array

def wait(*duration):
    # if a number is entered then wait that long and quit
    if type(duration) == int:
        print(f'Waiting for {duration}')
        time.sleep(duration)
        return
    now = datetime.now()
    timestamp1 = int(round(time.time()))
    r = getCalendar(f'{now.year}-{now.month}-{now.day}',f'{now.year}-{now.month+1}-01')
    date = datetime.strftime(r[1].date,'%Y-%m-%d')
    dt = datetime(int(date[0:4]),int(date[5:7]),int(date[8:10]),9,30)
    seconds = int(round(dt.timestamp())) - timestamp1
    print(f'Going to sleep for {seconds} seconds')
    time.sleep(seconds)

def calcProfit(starting_balance,stock):
    try:
        df1 = pd.read_csv(f'stock_objs/{stock}/sellPrices.csv')
    except:
        return False
    balance = starting_balance
    for n in df1.index:
        row = df1.loc[n]
        trade_type = row['type']
        price = row['change']
        if n == df1.index[-1]:
            if trade_type == 'buy':
                break
        if trade_type == 'buy':
            balance -= price
        else:
            balance += price
    print(f'Final balance: {balance}, Profit: {balance-starting_balance}')