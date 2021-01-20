import pandas as pd
from datetime import datetime

def startup():
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
