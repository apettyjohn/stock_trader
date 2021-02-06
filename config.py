from api_keys import POLYGON_API_KEY, POLYGON_BASE_URL
from pandas._libs.tslibs import Timestamp
from alpaca import getCalendar
import pandas as pd
import numpy as np
import matplotlib.pyplot as plot
from mpl_finance import candlestick_ohlc
import requests, time, json,pytz
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
    polygon_min = {}
    polygon_hour = {}
    watchlist_max_length = 1
    now = datetime.now()
    day = str(now.day-1)
    if int(day) < 10:
        day = '0'+day
    url = POLYGON_BASE_URL+"/v2/aggs/ticker/{}/range/{}/{}/{}/{}?apiKey={}"
    df1 = pd.read_csv('allSymbols.csv')
    df1.sort_values(by=['Volatility','% Change'],inplace=True,ascending=False)
    # saving only the top max_length ammount
    print('Getting Stock Data')
    for i in tqdm(range(watchlist_max_length), desc="Loading..."):
        n = df1.index[i]
        symbol = df1['Symbol'][n]
        check = True
        while check:
            polygon_min = json.loads(requests.get(url.format(symbol,5,'minute',now.strftime('%Y-%m-%d')[0:-2]+day,now.strftime('%Y-%m-%d'),POLYGON_API_KEY)).content)
            polygon_hour = json.loads(requests.get(url.format(symbol,1,'hour',now.strftime('%Y-%m-%d')[0:-2]+day,now.strftime('%Y-%m-%d'),POLYGON_API_KEY)).content)
            status = polygon_hour['status']
            #print(status)
            if status == 'ERROR':
                #print('exceeded rate limit,sleeping for 3 sec')
                time.sleep(3)
            else:
                check = False
        # convert json from response into a dataframe
        data = []
        for n in range(polygon_min['resultsCount']):
            row = polygon_min['results'][n]
            data.append([row['o'],row['h'],row['l'],row['c'],row['v'],row['t']/1000])
        min_data = pd.DataFrame(data,columns=['open','high','low','close','volume','time'])
        data = []
        for n in range(polygon_hour['resultsCount']):
            row = polygon_hour['results'][n]
            data.append([row['o'],row['h'],row['l'],row['c'],row['v'],row['t']/1000])
        hour_data = pd.DataFrame(data,columns=['open','high','low','close','volume','time'])
        # if there's enough data add it to the list
        if len(min_data.index) > 5 and len(hour_data.index) > 1:
            watchlist.append([symbol,df1['Price'][n],df1['Volatility'][n],df1['% Change'][n],df1['Volume'][n]])
            stock = Stock(symbol,min_data,hour_data)
            StockObjs(stock,'a')
        else:
            watchlist_max_length += 1
    df2 = pd.DataFrame(watchlist,columns=df1.columns)
    df2.to_csv('watchlist.csv',index=False)
    print('Successfully created watchlist')

class Stock:
    def __init__(self,ticker,minuteData,hourData):
        self.ticker = ticker
        self.min_data = minuteData
        self.hour_data = hourData
        # how much data is in each dataframe
        self.minute_count = len(minuteData.index)
        self.hour_count = len(hourData.index)
    
    def plot(self):
        df1 = self.min_data
        df2 = self.hour_data
        new_df1 = df1.loc[:,['time','open','high','low','close']]
        new_df2 = df2.loc[:,['time','open','high','low','close']]
        new_df1.reset_index(inplace=True,drop=True)
        new_df2.reset_index(inplace=True,drop=True)
        x = np.linspace(0,len(df2.index),len(df2.index))
        plots = 3
        fig = plot.figure()
        fig.suptitle(self.ticker)
        for i in range(plots):
            if i == 0:
                axs1 = fig.add_subplot(3,1,1)
                candlestick_ohlc(axs1,new_df1.values, width=0.5, colorup='green', colordown='red', alpha=0.8)
                axs1.grid(True) 
                #axs1.title.set_text('Minute(s) increment')
            elif i == 1:
                axs2 = fig.add_subplot(3,1,2)
                candlestick_ohlc(axs2,new_df2.values, width=1, colorup='green', colordown='red', alpha=0.8)
                axs2.grid(True) 
                #axs2.title.set_text('Hour(s) increment')
            elif i == 2:
                axs3 = fig.add_subplot(3,1,3)
                axs3.grid(True) 
                axs3.bar(x,df2['volume'],label='volume')
                #axs3.title.set_text('Volume')
        plot.show()
    
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
