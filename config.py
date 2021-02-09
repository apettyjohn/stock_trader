from api_keys import POLYGON_API_KEY, POLYGON_BASE_URL
from alpaca import getCalendar
import pandas as pd
import requests, time, json, os
from datetime import datetime
from lxml import html
from alpaca import api
from tqdm import tqdm 
from stocks import *

Stocks = []
url = POLYGON_BASE_URL+"/v2/aggs/ticker/{}/range/{}/{}/{}/{}?apiKey={}"

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

def create_stock_objs():
    # Variables
    print('creating stock objs')
    stocks = os.listdir('stock_objs')
    # creating stock objects
    for i in tqdm(range(len(stocks)), desc="Loading..."):
        minDf = pd.read_csv(f'stock_objs/{stocks[i]}/min_data.csv')
        hourDf = pd.read_csv(f'stock_objs/{stocks[i]}/hour_data.csv')
        stock = Stock(stocks[i],minDf,hourDf)
        addStockObjs(stock,'a')
    print('Successfully created watchlist')

def save_stocks():
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
    df1.sort_values(by=['Volatility','% Change'],inplace=True,ascending=False)
    # variables
    polygon_min = {}
    polygon_hour = {}
    watchlist_max_length = 20
    now = datetime.now()
    day = str(now.day-1)
    if int(day) < 10:
        day = f'0{day}'
    # loop through dataframe and save data
    for i in tqdm(range(watchlist_max_length), desc="Loading..."):
        n = df1.index[i]
        symbol = df1['Symbol'][n]
        check = True
        try:
            os.mkdir(f'stock_objs/{symbol}')
        except:
            # skip repeats
            watchlist_max_length += 1
            continue
        # make api call to polygon.io
        while check:
            polygon_min = json.loads(requests.get(url.format(symbol,5,'minute',now.strftime('%Y-%m-%d')[0:-2]+day,now.strftime('%Y-%m-%d'),POLYGON_API_KEY)).content)
            polygon_hour = json.loads(requests.get(url.format(symbol,1,'hour',now.strftime('%Y-%m-%d')[0:-2]+day,now.strftime('%Y-%m-%d'),POLYGON_API_KEY)).content)
            status = polygon_hour['status']
            if status == 'ERROR':
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
        # save dataframes into csv files
        with open(f'stock_objs/{symbol}/min_data.csv','w') as f:
            min_data.to_csv(f)
        with open(f'stock_objs/{symbol}/hour_data.csv','w') as f:
            hour_data.to_csv(f)

# Trading Strategy Functions
def updateHourData():
    Stocks = getStockObjs()
    for stock in Stocks:
        symbol = stock.ticker
        now = datetime.now()
        day = str(now.day-1)
        if int(day) < 10:
            day = '0'+day
        polygon_hour = json.loads(requests.get(url.format(symbol,1,'hour',now.strftime('%Y-%m-%d')[0:-2]+day,now.strftime('%Y-%m-%d'),POLYGON_API_KEY)).content)
        last_row = polygon_hour['results'][len(polygon_hour['results'])-1]
        stock.addData([last_row['o'],last_row['h'],last_row['l'],last_row['c'],last_row['v'],last_row['t']/1000])
