import pandas as pd
from datetime import datetime
import os,time,requests,json
import alpaca_trade_api as tradeapi

# Environment variables
PAPER_API_KEY = 'PKS5DDOD4FZ0CJ9NMI0I'
PAPER_API_SECRET_KEY = 'omjVk7zs520TS2ONT8twl4ayfo3ltuH1lnj4nGfY'
LIVE_API_KEY = 'AKRF2GZWS2CLQSOK5KV9'
LIVE_API_SECRET_KEY = 'vu3VUtZlQeToIuhGZ6DIIIiPf6Q1YXIGJyb5a9ER'
rate_limit = 200

response = response = input('Paper or live trading: ')
if response == 'live':
    BASE_URL = "https://api.alpaca.markets"
    HEADERS = {'APCA-API-KEY-ID':LIVE_API_KEY,'APCA-API-SECRET-KEY':LIVE_API_SECRET_KEY}
    api = tradeapi.REST(LIVE_API_KEY, LIVE_API_SECRET_KEY, api_version='v2')
elif response == 'paper':
    BASE_URL = "https://paper-api.alpaca.markets" 
    HEADERS = {'APCA-API-KEY-ID':PAPER_API_KEY,'APCA-API-SECRET-KEY':PAPER_API_SECRET_KEY}
    api = tradeapi.REST(PAPER_API_KEY, PAPER_API_SECRET_KEY, api_version='v2')
else:
    raise KeyError

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
    r = requests.get(ACCOUNT_URL + '/portfolio/history',headers=HEADERS)
    return json.loads(r.content)

# Order Functions
def getOrder(id):
    if id == 'all':
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
    return json.loads(r.content)

# Position Functions
def getPosition(id):
    if id == 'all':
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
def getWatchlist(id):
    if id == 'all':
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
    return json.loads(r.content)

# Calendar Functions
def getCalendar(start_date,end_date):
    # dates must be in "%Y-%m-%d" format
    r = requests.get(CALENDAR_URL,json={'start':start_date,'end':end_date},headers=HEADERS)
    return json.loads(r.content)

# Clock Functions
def marketOpen():
    r = requests.get(CLOCK_URL,headers=HEADERS)
    return json.loads(r.content)['is_open']
def getClock():
    r = requests.get(CLOCK_URL,headers=HEADERS)
    return json.loads(r.content)

# Other Functions
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
                # if new data is older than saved data
                if data[i] < switchDate(df['Date'][0]):
                    df.loc[n] = pd.Series([switchDate(data[i].t),data[i].o,data[i].h,data[i].l,data[i].c,data[i].v])
                    n = n-1
                # if new data is newer than saved data
                if data[i] > switchDate(df['Date'][len(df['Date'])-1]):
                    new.append = [switchDate(data[i].t),data[i].o,data[i].h,data[i].l,data[i].c,data[i].v]
            df.index = df.index + (-1*(n+1))
            df = df.sort_index()
            if len(new) > 0:
                for row in new.reverse():
                    df = df.append(pd.Series(row,index=[df.columns]),ignore_index=True)
    except FileNotFoundError: 
        df = pd.DataFrame([[switchDate(data[0].t),data[0].o,data[0].h,data[0].l,data[0].c,data[0].v]],columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        for bar in data:
            df = df.append(pd.Series([switchDate(bar.t),bar.o,bar.h,bar.l,bar.c,bar.v],index=[df.columns]),ignore_index=True)
    # Save dataframe to a csv file
    df.to_csv(f'stock_profiles/historical/{ticker}.csv')
    return f'Successfully got data for {ticker}'
def switchDate(s):
    # converts between integer and string date formats
    if type(s) == str:
        return time.mktime(datetime.datetime.strptime(s, "%m/%d/%Y").timetuple())
    elif type(s) == int:
        return datetime.fromtimestamp(s).strftime('%-m/%-d/%Y %H:%M:%S')[0:9]
