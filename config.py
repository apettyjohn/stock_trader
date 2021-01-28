import pandas as pd
from datetime import datetime
from lxml import html
import requests, os, time


def wait(*duration):
    # FIXME: account for timezone changes

    # if a number is entered then wait that long and quit
    if type(duration) == int:
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

def txt2csv(location,delimiter,output):
    # turns the nasdaq text lists into a csv of trading symbols
    try:
        # if the text file has already been parsed then quit
        csv_file = open(f'{output}.csv','r')
        print(f'Csv file already exists for {location}.txt file')
        return
    except:
        # open text file and put data in list
        file = open(f'{location}.txt','r')
        lines = file.readlines()
        columns = []
        print('Beginning txt to csv conversion')
        columns = lines[0].split(f'{delimiter}')[0]
        data = lines[1].split(f'{delimiter}')
        df = pd.DataFrame([[data[0]]],columns=[columns])
        for n in range(len(lines)):
            line = lines[n]
            data = line.split(f'{delimiter}')
            # save rows as data series
            if n == len(lines)-1:
                file = open(f'{output}.csv',"w")
                break
            else:
                df = df.append(pd.Series([data[0]],index=[columns]),ignore_index=True)
        df.to_csv(f'{output}.csv',index=False)
        print(f'Successfully converted {location}.txt to {output}.csv')

def clean_symbols():
    # removes garbage data from stock_profiles folder
    print('Cleaning symbol list')
    path = os.getcwd() + "/stock_profiles/historic/"

    for filename in os.listdir(path):
        for char in filename:
            # if there is a $ in the name remove it
            if char == '$':
                os.remove(os.path.join(path,filename))
                print(f'Deleted {filename}')
                break
        try:
            df = pd.read_csv(os.path.join(path,filename))
            # if it's not formatted properly remove it
            if df.columns[0] != 'Date':
                os.remove(os.path.join(path,filename))
                print(f'Deleted {filename}')
        except:
            try:
                # if the file exists but can't be read by pandas remove it
                f = open(os.path.join(path,filename))
                os.remove(os.path.join(path,filename))
                print(f'Deleted {filename}')
            except:
                pass
    else:
        print('No files needed removing')

