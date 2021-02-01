from logging import error
import pandas as pd
from datetime import datetime
import os,time,requests,json
import alpaca_trade_api as tradeapi
from api_keys import *

# Environment variables
rate_limit = 200

#BASE_URL = "https://api.alpaca.markets" #--live account url
BASE_URL = "https://paper-api.alpaca.markets" # --paper account url
HEADERS = {'APCA-API-KEY-ID':API_KEY,'APCA-API-SECRET-KEY':API_SECRET_KEY}
api = tradeapi.REST(API_KEY, API_SECRET_KEY, api_version='v2')

ACCOUNT_URL = "{}/v2/account".format(BASE_URL)
ORDERS_URL = '{}/v2/orders'.format(BASE_URL)
CLOCK_URL = '{}/v2/clock'.format(BASE_URL)
POSITIONS_URL = '{}/v2/positions'.format(BASE_URL)
ASSETS_URL = '{}/v2/assets'.format(BASE_URL)
CALENDAR_URL = '{}/v2/calendar'.format(BASE_URL)
WATCHLIST_URL = '{}/v2/watchlists'.format(BASE_URL)

# Account Functions
def checkAccount():
    # return account info
    r = requests.get(ACCOUNT_URL,headers=HEADERS)
    return json.loads(r.content)
def getAccountConfigs():
    r = requests.get(ACCOUNT_URL + '/configurations',headers=HEADERS)
    return json.loads(r.content)
def updateAccountConfigs(data):
    r = requests.patch(ACCOUNT_URL + '/configurations',json=data,headers=HEADERS)
    return json.loads(r.content)
def portfolioHistory(parameters):
    # Parameters include:
    # period - The duration of the data in <number>+<unit>, D for day, W for week, M for month and A for year
    # timeframe - The resolution of time window. 1Min, 5Min, 15Min, 1H, or 1D
    # date_end - in “YYYY-MM-DD” format. Default is current day
    # extended_hours - bool, timeframe must be < 1D
    r = requests.get(ACCOUNT_URL + '/portfolio/history',json=parameters,headers=HEADERS)
    return json.loads(r.content)

# Order Functions
def getOrder(*id):
    if type(id) == None:
        r = requests.get(ORDERS_URL,headers=HEADERS)
    else:
        r = requests.get(ORDERS_URL + '/{}'.format(id),headers=HEADERS)
    return json.loads(r.content)
def postOrder(symbol,qty,side,type,time_in_force,other_field='',other_field_value=0,extended_hrs=False):
    data = {
        'symbol':symbol,
        'qty':qty,
        'side':side,
        'type':type,
        'time_in_force':time_in_force,
    }
    if other_field:
        data[f'{other_field}'] = other_field_value
    if extended_hrs:
        if type == 'limit' and time_in_force == 'day':
            data['extended_hours'] = True
    r = requests.post(ORDERS_URL,json=data,headers=HEADERS)
    return json.loads(r.content)
def patchOrder(id,update_fields):
    r = requests.patch(ORDERS_URL + '/{}'.format(id),json=update_fields,headers=HEADERS)
    return json.loads(r.content)
def deleteOrder(id):
    if id == 'all':
        r = requests.delete(ORDERS_URL,headers=HEADERS)
    else:
        r = requests.delete(ORDERS_URL + f'/{id}',headers=HEADERS)
    return (r.content)

# Position Functions
def getPosition(*id):
    if type(id) == None:
        r = requests.get(POSITIONS_URL,headers=HEADERS)
    else:
        r = requests.get(POSITIONS_URL + '/{}'.format(id),headers=HEADERS)
    return json.loads(r.content)
def deletePosition(id):
    if id == 'all':
        r = requests.delete(POSITIONS_URL,headers=HEADERS)
    else:
        r = requests.delete(POSITIONS_URL + f'/{id}',headers=HEADERS)
    return json.loads(r.content)

# Asset Functions
def getAsset(id):
    if type(id) == str:
        r = requests.get(ASSETS_URL + '/{}'.format(id),headers=HEADERS)
    elif type(id) == int:
        r = requests.get(ASSETS_URL + '/:{}'.format(id),headers=HEADERS)
    else:
        r = "Invalid input for getAsset()"
    return json.loads(r.content)

# Watchlist Functions
def getWatchlist(*id):
    if type(id) == None:
        r = requests.get(WATCHLIST_URL,headers=HEADERS)
    else:
        r = requests.get(WATCHLIST_URL + '/{}'.format(id),headers=HEADERS)
    return json.loads(r.content)
def newWatchlist(name,symbols=[]):
    r = requests.post(WATCHLIST_URL,json={'name':name,'symbols':symbols},headers=HEADERS)
    return json.loads(r.content)
def updateWatchlist(id,*name,symbols=[]):
    r = requests.get(WATCHLIST_URL + '/{}'.format(id),headers=HEADERS)
    if type(name) == None:
        name = r['name']
    r = requests.put(WATCHLIST_URL + '/{}'.format(id),json={'name':name,'symbols':symbols},headers=HEADERS)
    return json.loads(r.content)
def addWatchlistSymbol(id,symbol):
    r = requests.post(WATCHLIST_URL + '/{}'.format(id),json={'symbol':symbol},headers=HEADERS)
    return json.loads(r.content)
def removeWatchlistSymbol(id,symbol):
    r = requests.delete(WATCHLIST_URL + f'/{id}/{symbol}',headers=HEADERS)
    return json.loads(r.content)
def deleteWatchlist(id):
    r = requests.delete(WATCHLIST_URL + f'/{id}',headers=HEADERS)
    return (r.content)

# Calendar Functions
def getCalendar(start_date='',end_date=''):
    if start_date and end_date:
        print(start_date,end_date)
        # dates must be in "%Y-%m-%d" format
        r = api.get_calendar(start=start_date,end=end_date)
    else:
        r = api.get_calendar()
    return r

# Clock Functions
def getClock():
    r = requests.get(CLOCK_URL,headers=HEADERS)
    return json.loads(r.content)

# Other Functions
def getHistoricalData(ticker,frequency,days):
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
    # add the data to a dataframe
    try:
        df = pd.read_csv(f'stock_profiles/historical/{ticker}.csv')
        # compares current date with last date of stock data
        if compareDates(datetime.now().strftime('%Y-%m-%d'),df.loc[len(df.index)-1][3]):
            return (f'{ticker}.csv is up to date')
        else:
            raise ValueError
    except:
        # Pull data from API
        data = api.get_barset(ticker,frequency,limit=days).df[f'{ticker}']
        try:
            df = pd.DataFrame([[data['open'][0],data['high'][0],data['low'][0],data['close'][0],data['volume'][0]]],columns=['open','high','low','close','volume'])
            for n in range(1,len(data.index)):
                df = df.append(pd.Series([data['open'][n],data['high'][n],data['low'][n],data['close'][n],data['volume'][n]],index=df.columns),ignore_index=True)
            df.loc[-1] = ['From',f'{data.index[0]}','To',f'{data.index[len(data.index)-1]}','-']
            df.index.sort_values()
            # Save dataframe to a csv file
            df.to_csv(f'stock_profiles/historical/{ticker}.csv',index=False)
            return (f'Successfully got data for {ticker}')
        except:
            return (f'Couldn"t find data for {ticker}')

def compareDates(date1,date2):
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
