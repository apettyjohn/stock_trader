import requests,json,time,api_keys,math
import robin_stocks as rs
import robin_stocks.robinhood as rh
import alpaca_trade_api as tradeapi
from api_keys import *
import numpy as np

### Alpaca

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

# Other Functions
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
def getCalendar(start_date='',end_date=''):
    if start_date and end_date:
        # dates must be in "%Y-%m-%d" format
        r = api.get_calendar(start=start_date,end=end_date)
    else:
        r = api.get_calendar()
    return r
def getClock():
    r = requests.get(CLOCK_URL,headers=HEADERS)
    return json.loads(r.content)


### TD Ameritrade

base_url = 'https://api.tdameritrade.com/v1/marketdata/'

def td_priceHistory(symbol,mainInterval,num1,subInterval,num2):
    url = base_url+'{stock_ticker}/pricehistory?periodType={periodType}&period={period}&frequencyType={frequencyType}&frequency={frequency}'
    full_url = url.format(stock_ticker=symbol,periodType=mainInterval,period=num1,frequencyType=subInterval,frequency=num2)
    # Get request
    code = 0
    while code != 200:
        r = requests.get(url=full_url,params={'apikey':TD_API_KEY},headers={'Authorization':'Bearer '+get_TD_token()})
        code = r.status_code
        dict = json.loads(r.content)
        if code == 401:
            td_newToken()
            time.sleep(1)
        elif code == 403:
            time.sleep(2)
        elif code == 400:
            print('Bad request')
            break
    return dict

def td_getQuote(symbol):
    url = base_url+'quotes'
    payload = {
        'apikey':TD_API_KEY
    }
    if type(symbol) != str:
        symbols = ','.join(symbol)
        payload['symbol'] = symbols
    else:
        payload['symbol'] = symbol
    code = 0
    while round(code / 100,0) != 2:
        r = requests.get(url=url,params=payload,headers={'Authorization':'Bearer ' + get_TD_token()})
        code = r.status_code
        if code == 401:
            td_newToken()
            time.sleep(0.5)
        elif round(code / 100,0) == 4:
            print(f'Bad request. Status code={code}')
            break
        else:
            print(f'Unknown error. Status code={code}')
            break
    return r

def td_newToken():
    url = 'https://api.tdameritrade.com/v1/oauth2/token'
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token':REFRESH_TOKEN,
        'client_id':TD_API_KEY,
        'code':'',
        'access_type':'',
        'redirect_uri':''
    }
    r = requests.post(url=url,data=payload)
    content = r.json()
    api_keys.change_TD_token(content['access_token'])
    print('New TD access token')
    return content

def td_newOrder(ticker,qty,instruction,qtyType='shares',duration='day'):
    url = f'https://api.tdameritrade.com/v1/accounts/498394233/orders'
    payload = {
        "orderType": "MARKET",
        "session": "NORMAL",
        "duration": duration.upper(),
        "orderStrategyType": "SINGLE",
        "orderLegCollection": [{
            "instruction": instruction.upper(),
            "quantity": qty,
            "quantityType":qtyType.upper(),    # Dollars or shares
            "instrument": {
                "symbol": ticker,
                "assetType": "EQUITY"
            }
        }]
    }
    code = 0
    while round(code / 100,0) != 2:
        r = requests.post(url=url,data=json.dumps(payload),headers={'Authorization':'Bearer '+get_TD_token(),'Content-Type':'application/json'})
        code = r.status_code
        if code == 401:
            td_newToken()
            time.sleep(0.5)
        elif round(code / 100,0) == 4:
            print(f'Bad request. Status code={code}')
            break
        elif round(code / 100,0) != 2:
            print(f'Unknown error. Status code={code}')
            break
    return r.content

def td_getOrder(maxResults=5,status=''):
    url = 'https://api.tdameritrade.com/v1/orders'
    payload = {
        'accountId':498394233,
        'maxResults':maxResults,
        'status':status.upper()     # Common statuses are filled,queued,canceled,expired,accepted,rejected,etc
    }
    code = 0
    while round(code / 100,0) != 2:
        r = requests.get(url=url,params=payload,headers={'Authorization':'Bearer ' + get_TD_token()})
        code = r.status_code
        if code == 401:
            td_newToken()
            time.sleep(0.5)
        elif round(code / 100,0) == 4:
            print(f'Bad request. Status code={code}')
            break
        elif round(code / 100,0) != 2:
            print(f'Unknown error. Status code={code}')
            break
    return json.loads(r.content)

#print(td_newOrder('AMC',1,'buy'))


### RobinHood
def rh_login():
    try:
        rh.login(username=rh_username,password=rh_password,expiresIn=86400,by_sms=True)
        print('Authenticated Robinhood API')
    except Exception as e:
        print("Error logging in:", e)

def rh_logout(signBackIn=False):
    try:
        rh.logout()
        print('Logged out of robinhood api')
        time.sleep(0.1)
    except Exception as e:
        print("Error logging out:", e)

    if signBackIn:
        rh_login()

def rh_marketOrder(symbol,shares,instruction):
    try:
        if instruction == 'buy':
            r = rh.order_buy_crypto_by_quantity(symbol,shares,jsonify=False) 
        elif instruction == 'sell':
            r = rh.order_sell_crypto_by_quantity(symbol,shares,jsonify=False)
        print(f'Order placed to {instruction} {shares} of {symbol}') 
    except Exception as e:
        print("Error placing market order:", e)
    return json.loads(r.content)

def rh_limitOrder(symbol,shares,ammountInDollars,instruction):
    try:
        if instruction == 'buy':
            r = rh.order_buy_crypto_limit(symbol,shares,ammountInDollars,jsonify=False)
        elif instruction == 'sell':
            r = rh.order_sell_crypto_limit(symbol,shares,ammountInDollars,jsonify=False)
    except Exception as e:
                print("Error placing limit order:", e)
    return json.loads(r.content)

def rh_getPrice(crypto):
    try:
        return rh.crypto.get_crypto_quote(crypto)
    except Exception as e:
        print("Error getting stock price:", e)

def rh_getHistoricalStockPrice(stock,interval='hour',span='week'):
    # Valid intervals: ['5minute', '10minute', 'hour', 'day', 'week']
    # Valid time spans: ['day', 'week', 'month', '3month', 'year', '5year']
    try:
        data = rh.get_stock_historicals(stock, interval=interval, span=span)
        return data
    except Exception as e:
        print("Error getting historical data:", e)

def rh_getHistoricalCryptoPrice(stock,interval='5minute',span='day'):
    # Valid intervals: ['15second', '5minute', '10minute', 'hour', 'day', 'week']
    # Valid time spans: ['hour', 'day', 'week', 'month', '3month', 'year', '5year']
    try:
        data = rh.crypto.get_crypto_historicals(stock, interval=interval, span=span)
        return data
    except Exception as e:
        print("Error getting historical data:", e)

def rh_positions(positionType):
    try:
        if positionType == 'stock':
            data = rh.orders.get_all_open_stock_orders()
        elif positionType == 'crypto':
            data = rh.orders.get_all_open_crypto_orders()
        else:
            data = rh.account.get_all_positions()
    except Exception as e:
        print('Error getting positions: ',e)
    return data

def trend(crypto,fractionOfDay=1):
    data = rh_getHistoricalCryptoPrice(crypto)
    print(len(data),math.ceil(len(data)*fractionOfDay))
    prices = []
    for num in data[-math.ceil(len(data)*fractionOfDay):]:
        prices.append((float(num['close_price'])+float(num['open_price']))/2)
    diffs = np.diff(prices)
    return round(sum(diffs),5)

# rh_login()
# #print(rh_getPrice('ETC'))
# print(rh.orders.get_all_crypto_orders()[0])
