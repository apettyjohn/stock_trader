import pandas as pd
from datetime import datetime
from datetime import date
import time
from lxml import html
import requests
import os
import alpaca_trade_api as tradeapi

def startup():
    account = api.get_account()
    return account,response
    
def tradingType():
    response = ''
    while response != 'live' and response != 'paper':
        response = input('Paper or live trading: ')
    return response

def marketOpen():
    clock = api.get_clock()
    return clock.is_open

def wait(*duration):
    if type(duration) == int:
        time.sleep(duration)
        return
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    today = datetime.today().weekday()
    if today >= 4:
        hours = ((6-today)*24) + (24-int(current_time[0:2])) + 9
    else:
        hours = (23-int(current_time[0:2])) + 9
    seconds = hours*3600 + (60-int(current_time[3:5]))*60
    print(f'Going to sleep for {seconds} seconds')
    time.sleep(seconds)
    open = marketOpen()
    while not(open):
        if open:
            print('Market is open')
            return
        time.sleep(60)
        open = marketOpen()

def pullIPOs():
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
    for n in list(range(len(symbols))):
        for i in list(range(len(fields))):
            field = fields[i]
            data[i] = field[n]
            if i == len(fields)-1:
                array.append(data)
    return array

def getHistoricalData(ticker,frequency,days):
    # Pull data from API
    data = api.get_barset(ticker,frequency,limit=days)[ticker]
    # check if folders exist
    try:
        files = os.listdir('stock_profiles/')
        for folder in ['historical','hour','minute','second']:
            if folder not in files:
                os.mkdir(f'stock_profiles/{folder}')
    except FileNotFoundError:
        os.mkdir('stock_profiles/')
        for folder in ['historical','hour','minute','second']:
            os.mkdir(f'stock_profiles/{folder}')
    # check if csv exists for input ticker
    try:
        df = pd.read_csv(f'stock_profiles/historical/{ticker}.csv')
        # remove adj close column if it exists
        try:
            df = df.drop(columns=['Adj Close'])
        except KeyError:
            pass
        # check if data is up to date
        if switchDate(df['Date'][0]) > data[0].t:
            n = -1
            new = []
            for i in range(days).reverse():
                if data[i] < switchDate(df['Date'][0]):
                    df.loc[n] = pd.Series([switchDate(data[i].t),data[i].o,data[i].h,data[i].l,data[i].c,data[i].v])
                    n = n-1
                if data[i] > switchDate(df['Date'][len(df['Date'])-1]):
                    new.append = [switchDate(data[i].t),data[i].o,data[i].h,data[i].l,data[i].c,data[i].v]
            df.index = df.index + (-1*(n+1))
            if len(new) > 0:
                for row in new.reverse():
                    df = df.append(pd.Series(row,index=[df.columns]),ignore_index=True)
    except FileNotFoundError: 
        df = pd.DataFrame([[switchDate(data[i].t),data[i].o,data[i].h,data[i].l,data[i].c,data[i].v]],columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        for bar in data:
            df = df.append(pd.Series([switchDate(bar.t),bar.o,bar.h,bar.l,bar.c,bar.v],index=[df.columns]),ignore_index=True)
        df.to_csv(f'stock_profiles/historical/{ticker}.csv')
    return 'Success'

def switchDate(s):
    if type(s) == str:
        return time.mktime(datetime.datetime.strptime(s, "%m/%d/%Y").timetuple())
    elif type(s) == int:
        return datetime.fromtimestamp(s).strftime('%-m/%-d/%Y %H:%M:%S')[0:9]

def txt2csv(location,delimiter,output,*noLastLine):
    try:
        csv_file = open(f'{output}.csv','r')
        print(f'Csv file already exists for {location}.txt file')
        return
    except:
        if not(noLastLine==True or noLastLine==False):
            noLastLine = False
        file = open(f'{location}.txt','r')
        lines = file.readlines()
        columns = []
        print('Beginning txt to csv conversion')
        for n in range(len(lines)):
            line = lines[n]
            if line:
                if n == 0:
                    first_line = line.split(f'{delimiter}')
                    columns = first_line[0]
                elif n == len(lines)-1:
                    file = open('output.csv',"w")
                    df.to_csv(f'{output}.csv',index=False)
                    if noLastLine:
                        print(f'Successfully converted {location}.txt to {output}.csv')
                        return
                else:
                    data = line.split(f'{delimiter}')
                    if n == 1:
                        df = pd.DataFrame([[data[0]]],columns=[columns])
                    else:
                        df = df.append(pd.Series([data[0]],index=[columns]),ignore_index=True)
        df.to_csv(f'{output}.csv',index=False)
        print(f'Successfully converted {location}.txt to {output}.csv')

def clean_symbols():
    print('Cleaning symbol list')
    
    # This is a terrrible idea to hardcode the path into the function
    path = "/mnt/c/Users/apett/Google Drive/Me/Documents/Programming/algorithmic-trading-python/stock_trader/stock_profiles"
    
    for filename in os.listdir(path):
        for char in filename:
            if char == '$':
                os.remove(f'stock_profiles/{filename}')
                print(f'Deleted {filename}')
                break
        try:
            df = pd.read_csv(f'stock_profiles/{filename}')
            if df.columns[0] != 'Date':
                os.remove(f'stock_profiles/{filename}')
                print(f'Deleted {filename}')
        except:
            try:
                f = open(f'stock_profiles/{filename}')
                os.remove(f'stock_profiles/{filename}')
                print(f'Deleted {filename}')
            except:
                pass
    else:
        print('No files needed removing')

# Environment variables
response = tradingType()
paper_key = ['PKKMPLCD1NJ4PBQRDIN1', 'rsWKwPZt1RDTpPwvIEd3Z84Kp4bf7FJDa1ZEM63S']
live_key = ['AKRF2GZWS2CLQSOK5KV9', 'vu3VUtZlQeToIuhGZ6DIIIiPf6Q1YXIGJyb5a9ER']
if response == 'live':
    os.environ["APCA_API_BASE_URL"] = "https://api.alpaca.markets"
    api = tradeapi.REST(live_key[0], live_key[1], api_version='v2')
else:
    os.environ["APCA_API_BASE_URL"] = "https://paper-api.alpaca.markets" 
    api = tradeapi.REST(paper_key[0], paper_key[1], api_version='v2')
rate_limit = 200