from alpaca import HEADERS
from datetime import datetime
import api_keys,json,requests

base_url = 'https://api.tdameritrade.com/v1/marketdata/'

def td_priceHistory(symbol,mainInterval,num1,subInterval,num2):
    url = base_url+'{stock_ticker}/pricehistory?periodType={periodType}&period={period}&frequencyType={frequencyType}&frequency={frequency}'
    full_url = url.format(stock_ticker=symbol,periodType=mainInterval,period=num1,frequencyType=subInterval,frequency=num2)
    # Get request
    r = requests.get(url=full_url,params={'apikey':api_keys.TD_API_KEY},headers={'Authorization':'Bearer '+api_keys.ACCESS_TOKEN})
    dict = json.loads(r.content)
    try:
        error = dict['error']
        td_newToken()
        r = requests.get(url=full_url,params={'apikey':api_keys.TD_API_KEY},headers={'Authorization':'Bearer '+api_keys.ACCESS_TOKEN})
        dict = json.loads(r.content)
    except:
        pass
    return dict

def td_getQuote(symbol):
    url = base_url+'quotes'
    payload = {
        'apikey':api_keys.TD_API_KEY
    }
    if type(symbol) != str:
        symbols = ','.join(symbol)
        payload['symbol'] = symbols
    else:
        payload['symbol'] = symbol
    r = requests.get(url=url,params=payload,headers={'Authorization':'Bearer '+api_keys.ACCESS_TOKEN})
    return r

def td_newToken():
    url = 'https://api.tdameritrade.com/v1/oauth2/token'
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token':api_keys.REFRESH_TOKEN,
        'client_id':api_keys.TD_API_KEY,
        'code':'',
        'access_type':'',
        'redirect_uri':''
    }
    r = requests.post(url=url,data=payload)
    content = r.json()
    api_keys.change_TD_token(content['access_token'])
    print(f'New TD access token:{content["access_token"]}')
    return content

