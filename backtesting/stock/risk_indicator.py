from ..stock_backtest import Backtest
from ..statistic import Statistic
import numpy as np
import pandas as pd
from stock_strategy import StockIndex

class RiskStrategyStatistic(Statistic):
    ma_window : int = 3
    upper_bound : float = 15
    lower_bound : float = 10
    forward_returns_days : int = 5

    def update_setting(self, setting):
        for key, value in setting.items():
            setattr(self, key, value)
        pass

    def generate_signal(self, data):
        """
        The function generates a signal based on the risk calculated from the given data.
        
        Args:
          data: The `data` parameter is a pandas DataFrame that contains the data needed to generate the
        signal. It is assumed to have a column named 'ticker' that represents the ticker symbol of each data
        point, and other columns that contain the necessary data for calculating the risk.
        
        Returns:
          a pandas DataFrame called "signal".
        """
        # generate signal
        risk = data.groupby('ticker').apply(calculate_risk, {'ma_window' : self.ma_window})
        risk = risk.swaplevel().squeeze().unstack()

        signal = pd.DataFrame(np.zeros(risk.shape), index=risk.index, columns=risk.columns)
        signal[(risk.shift(1) > self.upper_bound) & (risk < self.lower_bound)] = 1 
        signal = signal.reset_index().rename(columns={0 : 'date'})

        self.signal = signal
        return signal
    
    def generate_trade(self):

        data = self.kdata
        def calculate_forward_returns(data, params):
            return -1 * data.diff(-params['forward_returns_days']) / data
        
        forward_returns = data.set_index('date').groupby('ticker', group_keys = True)['close'].apply(
                                                calculate_forward_returns, 
                                                {'forward_returns_days' : self.forward_returns_days},
                                                )
        
        forward_returns = forward_returns.swaplevel().squeeze()
        self.signal.set_index('date').replace({0:np.nan}).stack()
        pass

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
            stop_sell = self.position.loc[self.position['price'] / self.position['cost'] - 1 < -0.05]
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

