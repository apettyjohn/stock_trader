from alpaca_trade_api.entity import Watchlist
import pandas as pd
import requests, time
from datetime import date, datetime
from requests.auth import HTTPBasicAuth 
from lxml import html
from alpaca import api
from tqdm import tqdm 

minStocks = []

# Foundation Functions
def wait(*duration):
    # if a number is entered then wait that long and quit
    if type(duration) == int:
        print(f'Waiting for {duration}')
        time.sleep(duration)
        return
    # otherwise wait until 9am on a weekday
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    today = datetime.today().weekday()
    if today >= 4:
        hours = ((6-today)*24) + (24-int(current_time[0:2])) + 9
    else:
        hours = (23-int(current_time[0:2])) + 9
    seconds = hours*3600 + (90-int(current_time[3:5]))*60
    print(f'Going to sleep for {seconds} seconds')
    time.sleep(seconds)

def pullIPOs():
    # pull the number and list of IPOs from yahoo finance
    print('Finding number of IPOs today')
    try:
        response = requests.get('https://finance.yahoo.com/calendar/ipo')
        if response.status_code == 200:
            print('Successfully pulled list')
        else:
            print(f'No response returned, status code: {response.status_code}')
    except:
        print(f'Http request failed. Check your connection')
        return
    tree = html.fromstring(response.content)
    num = tree.xpath('//*[@id="fin-cal-events"]/div[2]/ul/li[4]/a/text()')
    ipos = tree.xpath('//*[@id="cal-res-table"]/div[1]/table/tbody/tr/td[1]/a/text()')
    # returns number and full list of IPOs
    return [num[0],ipos]

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

def pullSymbols():
    print('Getting a list of symbols')
    allSymbols = []
    max_price = 10.0
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'}
    r = requests.get(f'https://finviz.com/screener.ashx?v=152&f=geo_usa,sh_opt_short,sh_price_u{int(max_price)}&r=0&c=0,1,5,6,49,50,51,52,65,66,67',headers=headers)
    tree = html.fromstring(r.content)
    pages = int(tree.xpath('//*[@id="screener-content"]/table/tr[7]/td/a[12]/text()')[0])
    # pull data from each page
    for n in tqdm (range(0,pages), desc="Loading..."):
        if n != 1:
            r = requests.get(f'https://finviz.com/screener.ashx?v=152&f=geo_usa,sh_opt_short,sh_price_u{int(max_price)}&r={n*20}&c=0,1,5,6,49,50,51,52,65,66,67',headers=headers)
            tree = html.fromstring(r.content)
        symbols = tree.xpath('//*[@id="screener-content"]/table/tr[4]/td/table/tr/td[2]/a/text()')
        prices = tree.xpath('//*[@id="screener-content"]/table/tr[4]/td/table/tr/td[9]/a/span/text()')
        change = tree.xpath('//*[@id="screener-content"]/table/tr[4]/td/table/tr/td[10]/a/span/text()')
        volume = tree.xpath('//*[@id="screener-content"]/table/tr[4]/td/table/tr/td[11]/a/text()')
        atr = tree.xpath('///*[@id="screener-content"]/table/tr[4]/td/table/tr/td[5]/a/text()')
        # fix volume data
        for i in range(len(volume)):
            if ',' in volume[i]:
                volume[i] = float(volume[i].replace(',',''))
        # fix % change data
        for i in range(len(change)):
            change[i] = float(change[i][0:-1])
        # fix prices data
        for i in range(len(prices)):
            prices[i] = float(prices[i])
        # fix atr data
        for i in range(len(atr)):
            atr[i] = float(atr[i])
        # only add data if it's affordable
        for i in range(len(prices)):
            if prices[i] < max_price:
                allSymbols.append([symbols[i],prices[i],atr[i],change[i],volume[i]])
    df = pd.DataFrame(allSymbols,columns=['Symbol','Price','ATR','% Change','Volume'])
    df.to_csv('allSymbols.csv',index=False)
    print('Successfully saved symbol list')
    print(f'Found {len(allSymbols)} symbols')

def avg_volume(df):
    timeframe = 14
    last_loc = len(df.index)-1
    volume = []
    if timeframe > len(df.index):
        timeframe = last_loc
    for n in range(timeframe):
        volume.append(float(df['volume'][df.index[last_loc-n]]))
    return sum(volume)/float(timeframe)

def percentATR(df):
    timeframe = 14
    last_loc = len(df.index)-1
    difference = []
    if timeframe > len(df.index):
        timeframe = last_loc
    for n in range(timeframe):
        high = df['high'][df.index[last_loc-n]]
        low = df['low'][df.index[last_loc-n]]
        difference.append(float(high)-float(low))
    atr = sum(difference)/timeframe
    return atr/float(df['close'][last_loc])

def sort_stocks():
    # Variables
    print('Sorting stocks')
    watchlist = []
    watchlist_max_length = 30
    now = datetime.now()
    start = pd.Timestamp(year = now.year,month = now.month,day = now.day-1,hour = 9, tz = 'US/Eastern').isoformat()
    # checking every symbol
    df1 = pd.read_csv('allSymbols.csv')
    df1.sort_values(by=['ATR'],inplace=True,ascending=False)
    # saving only the top max_length ammount
    print('Saving the watchlist')
    for n in df1.index[0:watchlist_max_length]:
        data = api.get_barset(df1['Symbol'][n],'1Min',start=start).df
        if len(data.index) > 30:
            watchlist.append([df1['Symbol'][n],df1['Price'][n],df1['ATR'][n],df1['% Change'][n],df1['Volume'][n]])
            stock = minuteData(df1['Symbol'][n],data)
            minObjs(stock,'a')
        else:
            watchlist_max_length += 1
    df2 = pd.DataFrame(watchlist,columns=df1.columns)
    df2.to_csv('watchlist.csv',index=False)
    print('Successfully created watchlist')

def getHistoricalData(ticker,frequency,days):
    data = api.get_barset(ticker,frequency,limit=days).df[f'{ticker}']
    try:
        df = pd.DataFrame([[data['open'][0],data['high'][0],data['low'][0],data['close'][0],data['volume'][0]]],columns=['open','high','low','close','volume'])
        for n in range(1,len(data.index)):
            df = df.append(pd.Series([data['open'][n],data['high'][n],data['low'][n],data['close'][n],data['volume'][n]],index=df.columns),ignore_index=True)
        #print(f'Successfully got data for {ticker}')
        if len(data.index) < 10:
            raise ZeroDivisionError
        return df
    except:
        return (f'Couldn"t find data for {ticker}')

class minuteData:
    def __init__(self,ticker,df):
        self.ticker = ticker
        self.df = df[self.ticker]
        self.timeframe = len(df.index)

def minObjs(obj=None,args=''):
    global minStocks
    if not(args):
        return minStocks
    else:
        if args == 'a':
            minStocks.append(obj)
        elif args == 'r':
            minStocks.remove(obj)
# Trading Strategy Functions
