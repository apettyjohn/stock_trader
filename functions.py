import pandas as pd
from datetime import datetime
from datetime import date
import time
from lxml import html
import requests
import csv
import os
import alpaca_trade_api as tradeapi

# Environment variables
os.environ["APCA_API_BASE_URL"] = "https://paper-api.alpaca.markets" 
paper_api = tradeapi.REST('PKW5BEJ43Z4MAPJQJDO2', '87rBVxc6ovavJU2LAwngQldDgD4c2ykwJx3l4S5S', api_version='v2')
live_api = tradeapi.REST('PK0Y84UA3R3OW8STP7QG', 'vu3VUtZlQeToIuhGZ6DIIIiPf6Q1YXIGJyb5a9ER', api_version='v2')

def startup():
    # Initiates a balance sheet if none exists and makes sure there is money to trade
    response = ''
    while response != 'live' and response != 'paper':
        response = input('Paper or live trading: ')
    if response == 'live':
        account = accountStatus('live')
    else:
        while response != 'local' and response != 'alpaca':
            response = input('Get balance from local or alpaca: ')
        if response == 'alpaca':
            account = accountStatus('paper')
        else:
            try:
                account = pd.read_csv('balance.csv')
            except:
                print('balance.csv did not exist')
                account = pd.DataFrame([['day trader',0]],columns=['Account','Balance'])
                account.to_csv('balance.csv',index=False)
                print('Created new balance.csv')
    return account,response
    
def marketOpen():
    clock = paper_api.get_clock()
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
    time.sleep(hours*60 + (60-int(current_time[3:5])))
    open = marketOpen()
    while not(open):
        if open:
            print('Market is open')
            return
        time.sleep(60)
        open = marketOpen()

def accountStatus(type):
    if type == 'paper':
        return paper_api.get_account()
    elif type == 'live':
        return live_api.get_account() 
    else:
        print(f'Invalid request for {type} account status')

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

def date2number(string,date):
    if date == 'dmy':
        format = "%d/%m/%Y"
    elif date == 'dym':
        format = "%d/%Y/%m"
    elif date == 'mdy':
        format = "%m/%d/%Y"
    elif date == 'myd':
        format = "%m/%Y/%d"
    elif date == 'ymd':
        format = "%Y/%m/%d"
    elif date == 'ydm':
        format = "%Y/%d/%m"
    else:
        #print('Noticed custom date format')
        format = date
    try:
        timestamp = int(time.mktime(datetime.strptime(string,format).timetuple()))
    except:
        print('Date could not be converted to a number')
        return
    return timestamp

def getHistoricalData(ticker,frequency,yrs,*supress):

    def pullData(ticker,frequency,yrs,*supress):
        if not(supress==True or supress==False):
            supress = False
        time_string = f'{date.today().day}/{date.today().month}/{date.today().year - yrs}'
        timestamp = date2number(time_string,'dmy')
        today = date2number(f'{date.today().day}/{date.today().month}/{date.today().year}',"dmy")
        try:
            print(f'Get: request initiated for {ticker} data every {frequency} for {yrs} years')
            response = requests.get(f'https://query1.finance.yahoo.com/v7/finance/download/{ticker}?period1={timestamp}&period2={today}&interval={frequency}&events=history&includeAdjustedClose=true')
            if response.status_code == 200:
                if not(supress):
                    print('Successfully pulled data')
            else:
                print(f'No response returned, status code: {response.status_code}')
        except:
            print(f'Http request failed. Check your connection')
            return 
        return response

    try:
        df = pd.read_csv(f'stock_profiles/{ticker}.csv')
        print(f'Data already exists for stock {ticker} from {df["Date"][0]} through {df["Date"][len(df["Date"])-1]}')
        time_string = f'{date.today().day}/{date.today().month}/{date.today().year - yrs}'
        timestamp = date2number(time_string,'dmy')
        if date2number(df["Date"][0],'%Y-%m-%d') > timestamp:
            #x = input('Would you like to update [y/n]: ')
            #if x == 'y'or x == 'Y' or x == 'yes':
            response = pullData(ticker,frequency,yrs)
            f = open(f'stock_profiles/{ticker}.csv','w')
            f.write(response.text)
            f.close()
    except:
        response = pullData(ticker,frequency,yrs)
        f = open(f'stock_profiles/{ticker}.csv','w')
        f.write(response.text)
        f.close()

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