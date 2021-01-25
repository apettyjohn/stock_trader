import pandas as pd
from datetime import datetime
from datetime import date
import time
from lxml import html
import requests
import csv
import os

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