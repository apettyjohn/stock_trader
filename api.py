import requests,json,time,api_keys
import alpaca_trade_api as tradeapi
from api_keys import *

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
    r = requests.get(url=url,params=payload,headers={'Authorization':'Bearer ' + ACCESS_TOKEN})
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

