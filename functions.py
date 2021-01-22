import pandas as pd
from datetime import datetime
from lxml import html
import requests

def startup():
    # Initiates a balance sheet if none exists and makes sure there is money to trade
    try:
        df = pd.read_csv('balance.csv')
    except:
        print('balance.csv does not exist')
        data = [['day trader',0]]
        df = pd.DataFrame(data, columns=['Account','Balance'])
        df.to_csv('balance.csv', index=False)
        print('Initialized new balance sheet')
    balance_data = df.to_dict()
    dt_funds = balance_data['Balance'][0]
    print(f"Current Balance: ${dt_funds}")

def logTrade(time,ticker,buy,sell):
    # Initates a trade log if none exists and logs trades
    my_columns = ['Time','Ticker','Buy','Sell','Net']
    dt = datetime.fromtimestamp(time)
    try:
        df = pd.read_csv('trades.csv')
        df = df.append(pd.Series([dt,ticker,buy,sell,sell-buy],index=my_columns),ignore_index=True)
    except:
        print('trades.csv does not exist')
        file = open('trades.csv',"x")
        df = pd.DataFrame([[dt,ticker,buy,sell,sell-buy]],columns=my_columns)
        print('Initialized new trading record')
    df.to_csv('trades.csv',index=False)

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

    my_columns = ['Symbols','Full Name','Price','Change','% Change','Volume','Market Cap']
    fields = [symbols,full_name,price,change,percent_change,volume,mkt_cap]
    data = list(range(len(fields)))
    for n in list(range(len(symbols))):
        for i in list(range(len(fields))):
            field = fields[i]
            data[i] = field[n]
        try:
            df = df.append(pd.Series(data,index=my_columns),ignore_index=True)
        except:
            df = pd.DataFrame([data],columns=my_columns)

    df.to_csv(f'{type}.csv',index=False)

def checkBalance(Account):
    # Reads the balance of the input account from balance.csv
    df = pd.read_csv('balance.csv')
    data = df.to_dict()
    accounts = data['Account']
    for n in list(range(len(accounts))):
        if accounts[n] == Account:
            return data['Balance'][n]
    return 'NaN'

def updateBalance(Account,change):
    # modifies the balance of the input account in balance.csv by the input change
    old_balance = checkBalance(Account)
    if old_balance == 'NaN':
        print(f'Could not update the balance of {Account}')
        return
    df = pd.DataFrame([[Account,old_balance + change]], columns=['Account','Balance'])
    balance_sheet = pd.read_csv('balance.csv')
    data = balance_sheet.to_dict()
    accounts = data['Account']
    for n in list(range(len(accounts))):
        if accounts[n] != Account:
            df = df.append(pd.Series([accounts[n]],data['Balance'][n],index=['Account','Balance']),ignore_index=True)
    df.to_csv('balance.csv', index=False)
