import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.ndimage.filters import gaussian_filter1d

Stocks = []

class Stock:
    def __init__(self,ticker):
        self.ticker = ticker
        self.quotes = None
        self.n = 0
        self.y_smooth = []
        self.y_deriv1 = []
        self.y_deriv2 = []
    
    def addData(self,price):
        if type(self.quotes).__name__ == 'NoneType':
            self.quotes = pd.DataFrame([[int(self.n),price]],columns=['index','price'])
        else:
            self.quotes = self.quotes.append(pd.Series([int(self.n),price],index=self.quotes.columns),ignore_index=True)
        self.quotes.to_csv(f'stock_objs/{self.ticker}/quotes.csv',index=False)

    def plot(self):
        def regressions(x1,y1):
            y_smooth1 = gaussian_filter1d(y1, 3)
            y_deriv1 = gaussian_filter1d(y_smooth1,2,order=1)
            y_deriv2 = gaussian_filter1d(y_smooth1,2,order=2)
            fig, ax = plt.subplots(3)
            fig.suptitle(f'{self.ticker}')
            ax[0].plot(x1,y1,c='black',linewidth=1.0)
            ax[0].scatter(x1,y_smooth1,c='red',s=15)
            ax[1].scatter(x1,y_deriv1,c='blue',s=15)
            ax[2].scatter(x1,y_deriv2,c='blue',s=15)
            ax[0].grid()
            ax[1].grid()
            ax[2].grid()
            plt.show()
        def buySell(x1,y1,x_b,y_b,x_s,y_s):
            fig,ax = plt.subplots(3)
            fig.suptitle(f'{self.ticker}')
            ax[0].plot(y1,c='black',linewidth=1.0)
            ax[0].plot(self.y_smooth,c='blue',linewidth=2.0)
            ax[0].scatter(x_b,y_b,s=20,c='green') # buy
            ax[0].scatter(x_s,y_s,s=20,c='red') # sell
            ax[1].plot(self.y_deriv1)
            ax[2].plot(self.y_deriv2)
            ax[0].grid()
            ax[1].grid()
            ax[2].grid()
            plt.show()

        try:
            df1 = pd.read_csv(f'stock_objs/{self.ticker}/sellPrices.csv')
        except:
            return
        df2 = self.quotes
        x1 = np.array(range(len(df2.index)))
        y1 = []
        for x in df2['price']:
            y1.append(x)
        x2 = []
        y2 = []
        x3 = []
        y3 = []
        for x in range(len(df1.index)):
            if df1['type'][x] == 'buy':
                x2.append(df1['index'][x])
                y2.append(df1['change'][x])
            else:
                x3.append(df1['index'][x])
                y3.append(df1['change'][x])
        buySell(x1,y1,x2,y2,x3,y3)
        #regressions(x1,y1)

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
