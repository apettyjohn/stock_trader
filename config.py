from alpaca_trade_api.entity import Watchlist
import pandas as pd
import requests, os, time,math
from datetime import datetime
from lxml import html
from alpaca import api
from tqdm import tqdm 

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
    r = requests.get(f'https://www.marketwatch.com/tools/stockresearch/screener/results.asp?TradesShareEnable=True&TradesShareMin=0&TradesShareMax={int(max_price)}&PriceDirEnable=False&PriceDir=Up&LastYearEnable=False&TradeVolEnable=False&BlockEnable=False&PERatioEnable=False&MktCapEnable=False&MovAvgEnable=False&MovAvgType=Outperform&MovAvgTime=FiftyDay&MktIdxEnable=False&MktIdxType=Outperform&Exchange=All&IndustryEnable=False&Industry=Tobacco&Symbol=True&CompanyName=True&Price=True&Change=True&ChangePct=True&Volume=True&LastTradeTime=False&FiftyTwoWeekHigh=False&FiftyTwoWeekLow=False&PERatio=False&MarketCap=False&MoreInfo=True&SortyBy=Symbol&SortDirection=Ascending&ResultsPerPage=OneHundred&PagingIndex=0')
    tree = html.fromstring(r.content)
    page = tree.xpath('//*[@id="stockscreener"]/div[3]/div[1]/text()')[0].split(' ')
    pages = 0
    # get the page number out of a string
    for n in range(len(page)):
        if page[n] == 'of':
            pages = math.floor(float(page[n+1])/100)
            break
    # pull data from each page
    for n in tqdm (range (1,pages), desc="Loading..."):
        #print(f'Parsing page: {n}')
        if n != 1:
            r = requests.get(f'https://www.marketwatch.com/tools/stockresearch/screener/results.asp?TradesShareEnable=True&TradesShareMin=0&TradesShareMax={int(max_price)}&PriceDirEnable=False&PriceDir=Up&LastYearEnable=False&TradeVolEnable=False&BlockEnable=False&PERatioEnable=False&MktCapEnable=False&MovAvgEnable=False&MovAvgType=Outperform&MovAvgTime=FiftyDay&MktIdxEnable=False&MktIdxType=Outperform&Exchange=All&IndustryEnable=False&Industry=Tobacco&Symbol=True&CompanyName=True&Price=True&Change=True&ChangePct=True&Volume=True&LastTradeTime=False&FiftyTwoWeekHigh=False&FiftyTwoWeekLow=False&PERatio=False&MarketCap=False&MoreInfo=True&SortyBy=Symbol&SortDirection=Ascending&ResultsPerPage=OneHundred&PagingIndex={n*100}')
            tree = html.fromstring(r.content)
        symbols = tree.xpath('//*[@id="stockscreener"]/div[5]/table/tbody/tr/td[1]/a/text()')
        prices = tree.xpath('//*[@id="stockscreener"]/div[5]/table/tbody/tr/td[3]/text()') # type=float
        change = tree.xpath('//*[@id="stockscreener"]/div[5]/table/tbody/tr/td[5]/text()') # type=float
        volume = tree.xpath('//*[@id="stockscreener"]/div[5]/table/tbody/tr/td[6]/text()') # type=float
        # fix volume data
        for i in range(len(volume)):
            if ',' in volume[i]:
                volume[i] = float(volume[i].replace(',',''))
            elif '.' in volume[i]:
                volume[i] = float(volume[i][0:-1].replace('.',''))*1000000.0
        # fix % change data
        for i in range(len(change)):
            change[i] = float(change[i][1:-1])
        # fix prices data
        for i in range(len(prices)):
            if ',' in prices[i]:
                prices[i] = prices[i].replace(',','')
            prices[i] = float(prices[i])
        # only add data if it's affordable
        for i in range(len(symbols)):
            if prices[i] < max_price:
                allSymbols.append([symbols[i],prices[i],change[i],volume[i]])
    df = pd.DataFrame(allSymbols,columns=['Symbol','Price','% Change','Volume'])
    df.to_csv('allSymbols.csv',index=False)
    print('Successfully saved symbol list')
    print(f'Found {len(allSymbols)} symbols')

# Trading Strategy Functions
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
    watchlist_max_length = 50
    #timeframe = 50
    #df = getHistoricalData(symbol,'day',timeframe)
    # checking every symbol
    df1 = pd.read_csv('allSymbols.csv')
    df1.sort_values(by=['% Change'],inplace=True,ascending=False)
    # saving only the top max_length ammount
    print('Saving the watchlist')
    for n in df1.index[0:watchlist_max_length]:
        watchlist.append([df1['Symbol'][n],df1['Price'][n],df1['% Change'][n],df1['Volume'][n]])
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

#def compareDates(date1,date2):
    # standardize dates
    formats = ['%Y-%m-%d','%Y/%m/%d','%m-%d-%Y','%m/%d/%Y']
    for format in formats:
        try:
            date1 = datetime.timestamp(datetime.strptime(date1,''))
            print('date1 converted')
        except:
            pass
        try:
            date2 = datetime.timestamp(datetime.strptime(date1,''))
            print('date2 converted')
        except:
            pass
    # returns the newest date by comparing day month and year
    # assumes year-month-day format
    return (date1 > date2)

#def txt2csv(location,delimiter,output):
    # turns the nasdaq text lists into a csv of trading symbols
    def testSymbol(data):
        # tests if the ticker is a common stock
        return 'Common Stock' in data[1]
    
    print('Pulling text lists')
    file = open(f'{location}.txt','r')
    lines = file.readlines()
    columns = []
    print('Beginning txt to csv conversion')
    columns = lines[0].split(f'{delimiter}')[0]
    symbols = []
    # make dataframe
    for n in range(1,len(lines)):
        line = lines[n]
        data = line.split(f'{delimiter}')
        # save rows as data series
        if n == len(lines)-1:
            file = open(f'{output}.csv',"w")
            break
        else:
            if testSymbol(data):
                symbols.append([data[0]])
    df = pd.DataFrame(symbols,columns=[columns])
    df.to_csv(f'{output}.csv',index=False)
    print(f'Successfully converted {location}.txt to {output}.csv')

#def clean_symbols(file):
    # removes garbage data from stock_profiles folder
    print(f'Cleaning symbol list from {file}')
    df = pd.read_csv(file)
    for symbol in df[df.columns[0]]:
        for char in symbol:
            # if there is a bad symbol, remove it
            if char == '$' or char == '.' or char == ' ':
                df = df.drop(index=df[df[df.columns[0]]==symbol].index[0])
                #print(f'Deleted {symbol}')
                break
    df.to_csv(file,index=False)
    print('Successful clean')
