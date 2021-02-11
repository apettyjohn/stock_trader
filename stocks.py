#from mpl_finance import candlestick_ohlc
import numpy as np
import matplotlib.pyplot as plot
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
    
    def plot(self):
        df1 = self.min_data
        df2 = self.hour_data
        new_df1 = df1.loc[:,['time','open','high','low','close']]
        new_df2 = df2.loc[:,['time','open','high','low','close']]
        new_df1.reset_index(inplace=True,drop=True)
        new_df2.reset_index(inplace=True,drop=True)
        x = np.linspace(0,len(df2.index),len(df2.index))
        plots = 3
        fig = plot.figure()
        fig.suptitle(self.ticker)
        for i in range(plots):
            if i == 0:
                axs1 = fig.add_subplot(3,1,1)
                candlestick_ohlc(axs1,new_df1.values, width=0.5, colorup='green', colordown='red', alpha=0.8)
                axs1.grid(True) 
                #axs1.title.set_text('Minute(s) increment')
            elif i == 1:
                axs2 = fig.add_subplot(3,1,2)
                candlestick_ohlc(axs2,new_df2.values, width=1, colorup='green', colordown='red', alpha=0.8)
                axs2.grid(True) 
                #axs2.title.set_text('Hour(s) increment')
            elif i == 2:
                axs3 = fig.add_subplot(3,1,3)
                axs3.grid(True) 
                axs3.bar(x,df2['volume'],label='volume')
                #axs3.title.set_text('Volume')
        plot.show()
    
    def addData(self,list,num):
        if list == 'quotes':
            self.quotes.append(num)
        elif list == 'trades':
            self.trades.append(num)
        elif list == 'minBars':
            self.minBars.append(num)
        return True

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
