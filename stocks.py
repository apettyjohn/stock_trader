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
        self.direction = 0
        self.peak = 0
        self.trough = 0
        self.last = 0
        self.buyPrice = 0

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
