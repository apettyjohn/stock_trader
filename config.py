from pandas._libs.tslibs import Timestamp
from alpaca import getCalendar
import pandas as pd
import matplotlib.pyplot as plot
import requests, time
from datetime import datetime
from lxml import html
from alpaca import api
from tqdm import tqdm 

Stocks = []

# Foundation Functions
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
    max_price = 15.0
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
                if ',' in volume:
                    volume = float(volume.replace(',',''))
                volatile = tree.xpath(base_xpath.format(i,6,''))[0][0:-1]
                #print(symbol,prices,atr,change,volume)
                row = [symbol,float(prices),round(float(volatile),1),float(change[0:-1]),float(volume)]
                # only add data if it's affordable
                if float(prices) < max_price:
                    allSymbols.append(row)
            except:
                pass
    df = pd.DataFrame(allSymbols,columns=['Symbol','Price','Volatility','% Change','Volume'])
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
    df1.sort_values(by=['Volatility','% Change'],inplace=True,ascending=False)
    # saving only the top max_length ammount
    print('Saving the watchlist')
    for n in df1.index[0:watchlist_max_length]:
        symbol = df1['Symbol'][n]
        min_data = api.get_barset(symbol,'1Min',start=start).df[symbol]
        hour_data = api.get_barset(symbol,'15Min',start=start).df[symbol]
        for i in range(round(len(hour_data.index)/4)-2):
            hour_data.drop(hour_data.index[i+1:i+4],inplace=True)
        if len(min_data.index) > 30:
            watchlist.append([symbol,df1['Price'][n],df1['Volatility'][n],df1['% Change'][n],df1['Volume'][n]])
            stock = Stock(symbol,min_data,hour_data)
            StockObjs(stock,'a')
        else:
            watchlist_max_length += 1
    df2 = pd.DataFrame(watchlist,columns=df1.columns)
    df2.to_csv('watchlist.csv',index=False)
    print('Successfully created watchlist')

class Stock:
    def __init__(self,ticker,minuteData=None,hourData=None):
        self.ticker = ticker
        data1 = []
        for n in range(len(minuteData.index)):
            data1.append([minuteData['close'][n]])
        self.minData = pd.DataFrame(data1,columns=['price'])
        self.minute_count = len(data1)
        data2 = []
        for n in range(len(hourData.index)):
            data2.append([hourData['close'][n]])
        self.hourData = pd.DataFrame(data2,columns=['price'])
        self.hour_count = len(data2)
    
    def plot(self,df,title=''):
        column = df.columns[0]
        df.plot.line(y=column,title=title)
        plot.show(block=True)
    
    def add_data(self,df,num):
        self.df.append(pd.Series([num],index=self.df.index),ignore_index=True)
        return True

def StockObjs(obj=None,args=''):
    global Stocks
    if not(args):
        return Stocks
    else:
        if args == 'a':
            Stocks.append(obj)
        elif args == 'r':
            Stocks.remove(obj)

# Trading Strategy Functions
