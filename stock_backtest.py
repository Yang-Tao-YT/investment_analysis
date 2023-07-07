
from collections import defaultdict

# import backtrader as bt
import numpy as np
import pandas as pd

import config
from utils.basic import name_2_symbol, rename_dataframe, Bar
from option_strategy import Trading
from stock_strategy import StockIndex, barloader, stock_etf_hist_dataloader, ArrayManager, Indicator
from utils.plot import plot_kline_volume_signal_adept

def obtain_stock(symbol, setting : dict = None) -> StockIndex:
    stockindex = StockIndex()
    hist = stock_etf_hist_dataloader(symbol)
    hist = rename_dataframe(hist)
    hist['date'] = pd.to_datetime(hist['date']).dt.date
    stockindex.set_am(hist)
    setattr(stockindex, 'origin_data', hist.set_index('date')) 
    # update setting
    if setting is not None:
        stockindex.update_setting(setting=setting)
    return stockindex

class Position:
    price = 0
    size = 0
    cash = 0
    orders = []
    def __init__(self, cash = 0) -> None:
        self.cash = cash
        self.inital_balance = self.balance()

    def value(self):
        self._value = self.price * self.size
        return self._value

    def balance(self):
        return self.value() + self.cash

class TestStrategy:
    am : ArrayManager
    position : Position

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.date[0]
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self, datas : pd.DataFrame, indicator, cash =  100000):
        '''
        datas: pd.DataFrame columns为K线, index为时间'''
        self.datas = datas
        self.indicator = indicator
        self.date = self.datas.index
        self.position = Position(cash = cash)
        self.intra_trade_high = 0

    def next(self):
        self.log('Close, %.4f' % self.datas.close[0])
        self.log(self.indicator[0])
        
        #进场
        if self.indicator[0] < 12 :
            size = self.position.cash / self.datas.open[1]
            if size > 1:
                self.buy(size, self.datas.open[1])
                self.log(f'Create order at { self.datas.open[1]} with size {size}')      
        

        if self.position.size > 0:
            self.intra_trade_high = max(self.datas.high[0], self.intra_trade_high)
            long_stop = self.intra_trade_high*(1-10/100)

            if self.indicator[0] > 90:
                # if self.position.size > 0:
                    self.sell(self.position.size, self.datas.open[1])
                    self.intra_trade_high = 0
            # 回撤，退出趋势
            elif self.datas.close[0] <= long_stop:
                
                    self.sell(self.position.size, self.datas.open[1])
                    self.intra_trade_high = 0

    def run(self):
        for i in range(len(self.date) - 1):#按时间顺序执行next
            self.__data_adjust_every_step()
            self.next()    
        self.stop()

    def __data_adjust_every_step(self):
        '''每个时间段上对数据进行的修建操作'''
        # self.dataclose = self.dataclose[1:]\
        self.datas = self.datas.iloc[1:,:]
        self.date = self.date[1:]
        self.indicator = self.indicator[1:]


    def buy(self, size, price):
        '''take order'''
        direction = 1
        new_size = self.position.size + (size * direction)
        new_value = self.position.value() + (size * direction * price)
        new_price =  new_value / new_size
        self.position.price = new_price
        self.position.size = new_size
        self.position.cash = self.position.cash - direction * size * self.datas.open[1]
        self.order_notify(direction, size, price)

    def sell(self, size, price):
        '''take order'''
        direction = -1
        new_size = self.position.size + (size * direction)

        self.position.size = new_size
        self.position.cash = self.position.cash - direction * size * self.datas.open[1]
        self.order_notify(direction, size, price)

    def stop(self):
        self.log(self.position.size * self.datas.close[0] + self.position.cash)

    def order_notify(self, direction, size, price):
        self.position.orders.append([self.date[1], direction, size, price, self.position.size * self.datas.close[1] + self.position.cash])

    def conclusion(self):
        result = {}
        orders = pd.DataFrame(backtest.position.orders, columns = ['date', 'direction', 'size', 'price', 'balance'])
        result['total return'] = (self.position.size * self.datas.close[0] + self.position.cash) / self.position.inital_balance
        result['orders'] = orders[1]
        return 

if __name__ == '__main__':
    # load data
    data = obtain_stock('sh512480')
    data = rename_dataframe(data.origin_data)

    si = StockIndex()
    si.set_am(data)
    risk = si.risk()[1]
    risk.index = data.index
    risk[risk.isnull()] = None
    data = data.iloc[:, :6]
    # data.index = pd.to_datetime(data.index)

    backtest = TestStrategy(data, risk)
    backtest.run()
    backtest.position.orders
    backtest.position.balance()
    backtest.datas.close
    backtest.conclusion()
    result = pd.DataFrame(backtest.position.orders)

    1
