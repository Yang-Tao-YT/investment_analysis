from utils.basic import name_2_symbol, rename_dataframe, Bar
from collections import defaultdict
from backtesting.stock_backtest import Backtest
from data.database import _get_hs300_history
import numpy as np
import pandas as pd

import config

from stock_strategy import StockIndex
from utils.plot import plot_kline_volume_signal_adept


def get_put(data):
    return data.loc[(data.tradecode.str.contains('P'))]

class RiskStrategyBacktest(Backtest):
    signal : pd.DataFrame

    def __init__(self, signal : pd.DataFrame, **kwargs):
        self.signal = signal
        self.signal['date'] = pd.to_datetime(self.signal['date'])
        pass

    def on_bar(self, date, data : pd.DataFrame):
        """
        The function `on_bar` processes a signal for a given date, calculates the long positions based on
        the signal, and updates the long portfolio and position accordingly.
        
        Args:
          date: The `date` parameter represents the date for which the `on_bar` function is being called. It
        is used to filter the `signal` dataframe to get the relevant signals for that date.
          data: The `data` parameter is a DataFrame that contains the historical price data for various
        tickers. It has columns such as 'ticker', 'date', and 'close'. The 'ticker' column represents the
        stock ticker symbol, the 'date' column represents the date of the price data, and the
        """

        signal = self.signal.loc[self.signal['date'] == date].drop('date', axis=1).squeeze()

        # 入场规则
        if (signal == 1).any():
            signal = signal[signal == 1]
            long = signal.to_frame('percentage').reset_index().rename(columns={'index': 'ticker'})
            long['percentage'] = long['percentage'] / long['percentage'].sum()
            long['price'] = data.set_index('ticker')['close'].loc[long.ticker.values].values
            long['cost'] = long['price']
            long['shares'] = self.cash() * long['percentage'] //  long['cost']

            if (long['shares'] > 0).any():
                self.long_portfolio(long[['ticker', 'shares', 'price', 'cost']])

        self.update_portfolio(data.set_index('ticker')['close'])
        self.out_signal()
        pass
    
    def out_signal(self):
        '''out signal'''
        if self.position.set_index('ticker').drop('cash').shape[0] > 0:
            '''止损清仓'''
            stop_sell = self.position.loc[self.position['price'] / self.position['cost'] - 1 < -0.025]
            if not stop_sell.empty:
                self.short_portfolio(stop_sell)
            
            '''止盈清仓'''
            limit_sell = self.position.loc[self.position['price'] / self.position['cost'] - 1 > 0.05]
            if not limit_sell.empty:
                self.short_portfolio(limit_sell)
    
        return self.signal
    
def calculate_risk(data, setting):
        tool = StockIndex()
        tool.set_am(data)
        if setting is not None:
            tool.update_setting(setting=setting)

        risk = tool.risk()
        return risk.set_index(0)


def load_history_data(source = 'sina'):
    data = pd.read_csv(f'{config.path_to_save}/history/500etf.csv', index_col=0)
    def funs(strs):
        return strs[strs.rfind('M')-4 : strs.rfind('M')]
    data['expire_date'] = data['tradecode'].apply(funs)
    return data

def return_stockindex(symbol, setting : dict = None) -> StockIndex:
    print('rerun')
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

def load_history_data():
    data = {}
    for key, value in name_2_symbol.items():
        symbol = value
        data[symbol] =  pd.read_csv(f'{config.path_hist_k_data}/{symbol}.csv')
        print(symbol)
        print('----------------')

    return data

if __name__ == '__main__':

    # load data
    data = load_history_data()
    data = pd.concat(data).reset_index()
    data = data.rename(columns={'level_0': 'ticker',
                        '日期' : 'date',
                        '執行時間' : 'time',
                        '开盘' : 'open',
                        '收盘' : 'close',
                        '最高' : 'high',
                        '最低' : 'low',
                        '成交量' : 'volume',})
    # generate signal
    risk = data.groupby('ticker').apply(calculate_risk, {'ma_window' : 3})
    risk = risk.swaplevel().squeeze().unstack()

    signal = pd.DataFrame(np.zeros(risk.shape), index=risk.index, columns=risk.columns)
    signal[(risk.shift(1) > 15) & (risk < 10)] = 1
    signal = signal.reset_index().rename(columns={0 : 'date'})
    
    test = RiskStrategyBacktest(signal)
    test.load_config({
        'start_date' : '2018-01-01',
        'end_date' : '2022-12-31',
        'initial_account' : 10000})
    
    test.load_data(data)
    test.run()
    print(test.return_value_records())



    # data = rename_dataframe(data.origin_data)
    # data = data.iloc[:, :6]
    # data.index = pd.to_datetime(data.index)
    # cerebro = bt.Cerebro()
    # cerebro.addstrategy(TestStrategy)

    # data_feed = bt.feeds.PandasData(dataname=data,
    #                                 # fromdate=start_date,
    #                                 # todate=end_date
    #                                 )
    # cerebro.adddata(data_feed)

    # cerebro.broker.setcash(100000.0)

    # # Print out the starting conditions
    # print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # # Run over everything
    # cerebro.run()

    # # Print out the final result
    # print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # 1