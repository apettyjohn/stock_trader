import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

Stocks = []

class Stock:
    def __init__(self,ticker,minuteData,hourData):
        self.ticker = ticker
        self.min_data = minuteData
        self.hour_data = hourData
        self.quotes = []
        self.trades = []
        self.minBars = []
        self.direction = -1
        self.peak = 0
        self.trough = 0
        self.last = 0
        self.buyPrice = 0
        self.buyIndex = 0
        self.quoteNum = 0
    
    def addData(self,price):
        try:
            df = pd.read_csv(f'stock_objs/{self.ticker}/quotes.csv')
            df = df.append(pd.Series([self.quoteNum,price],index=df.columns),ignore_index=True)
        except:
            df = pd.DataFrame([[int(self.quoteNum),price]],columns=['index','price'])
        df.to_csv(f'stock_objs/{self.ticker}/quotes.csv',index=False)
        self.quoteNum += 1

    def plot(self):
        try:
            df1 = pd.read_csv(f'stock_objs/{self.ticker}/quotes.csv')
            df2 = pd.read_csv(f'stock_objs/{self.ticker}/sellPrices.csv')
        except:
            return False
        x1 = []
        y1 = []
        for x in df1.index:
            x1.append(df1['index'][x])
            y1.append(df1['price'][x])
        x2,y2,x3,y3 = []
        for x in df2.index:
            if type(x) != str:
                x2.append(int(df2['index2'][x]))
                y2.append(df2['sell'][x])
                x3.append(int(df2['index1'][x]))
                y3.append(df2['buy'][x])

        plt.scatter(x1,y1,s=10,c='blue')
        plt.scatter(x2,y2,s=15,c='green')
        plt.scatter(x3,y3,s=15,c='red')
        plt.show()

def addStockObjs(obj=None,args=''):
    global Stocks
    if obj:
        if args == 'a':
            Stocks.append(obj)
        elif args == 'r':
            Stocks.remove(obj)
    else:
        return Stocks

def getStockObjs(ticker = ''):
    if ticker:
        for stock in Stocks:
            if stock.ticker == ticker:
                return stock
    else:
        return Stocks
