'''
backtesting 框架'''
import pandas as pd

class _BacktestUtils:
    position = pd.DataFrame(columns=['ticker', 'shares', 'price', 'cost'])

    def calculate_position_value(self):
        return self.position['shares'].dot(self.position['price'])
    
class Backtest(_BacktestUtils):

    start_date = ''
    end_date = ''
    kdata = pd.DataFrame()
    position = pd.DataFrame(columns=['ticker', 'shares', 'price', 'cost'])
    initial_account = 0
    total_value = 0
    total_profit = 0
    total_value_record = {}
    total_profit_record = {}

    def __init__(self) -> None:
        pass
    
    def load_data(self, kdata : pd.DataFrame):
        """
        The function `load_data` renames the columns of a DataFrame and converts the 'date' column to
        datetime format.
        
        Args:
          kdata (pd.DataFrame): kdata is a pandas DataFrame containing stock market data. It has the
        following columns:
        """
        kdata = kdata.rename(
            columns = { '日期' : 'date',
                        '執行時間' : 'time',
                        '开盘' : 'open',
                        '收盘' : 'close',
                        '最高' : 'high',
                        '最低' : 'low',
                        '成交量' : 'volume',}
        )
        kdata['date'] = pd.to_datetime(kdata['date'])
        self.kdata = kdata

    def load_config(self, config : dict = None):
        """
        The function `load_config` takes a dictionary as input and sets the attributes of the object to the
        corresponding values in the dictionary.
        
        Args:
          config (dict): The `config` parameter is a dictionary that contains key-value pairs. Each key
        represents a configuration option, and the corresponding value represents the value for that
        configuration option.
        """
        if config is not None:
            for key in config:
                setattr(self, key, config[key])

    def cash(self):
        """
        The code defines a function named "cash" that returns the number of shares of cash in a position,
        and a function named "on_bar" that takes in a date and data as parameters but does not have any code
        inside it.
        
        Returns:
          The `cash` method is returning the number of shares of cash held in the `position` DataFrame.
        """
        return self.position.loc[self.position['ticker'] == 'cash', 'shares'].squeeze()

    def on_bar(self, date, data):
        """
        The function "on_bar" takes in a date and data as parameters and does nothing.
        
        Args:
          date: The date parameter represents the date of the bar event. It could be a specific date or a
        timestamp indicating when the bar event occurred.
          data: The "data" parameter in the "on_bar" function is a variable that represents the data
        received for a specific date. The exact format and content of the data would depend on the context
        and purpose of the function. It could be a list, dictionary, or any other data structure that
        contains relevant
        """
        pass
    
    def return_value_records(self):
        return pd.Series(self.total_value_record)

    def update_portfolio(self, price : pd.Series):
        position = self.position.set_index('ticker')
        price = position.join(price)[price.name]
        position['price'] = price
        position.loc['cash', 'price'] = 1
        self.position = position.reset_index()
        pass

    def run(self):

        data = self.kdata
        index = pd.DatetimeIndex( data['date']).unique()
        index = index[(index >= self.start_date) & (index <= self.end_date)]
        data = data.sort_values(by=['date'])
        # inital position
        self.position.loc[0] = ['cash' ,self.initial_account, 1, 1]

        self.total_value = self.calculate_position_value()

        for _index in index:
            print(_index)
            on_bar_data = data.loc[data['date'] == _index]
            self.on_bar(_index, on_bar_data)
            self.total_value = self.calculate_position_value()
            self.total_value_record[_index] = self.total_value
            # pass
        
        self.return_value_records()
        return 
    
    def long(self, ticker, shares, price):
        if ticker in self.position.ticker.values:
            # calculate total value of position
            total_value = (self.position.loc[self.position.ticker == ticker, 'shares'] * 
                                                                    self.position.loc[self.position.ticker == ticker, 'cost'])
            total_value += shares * price

            # plus new share
            self.position.loc[self.position.ticker == ticker, 'shares'] += shares

            # calculate average cost of position
            self.position.loc[self.position.ticker == ticker, 'cost'] = total_value / self.position.loc[self.position.ticker == ticker, 'shares']
     
            
        else:
            self.position.loc[len(self.position)] = [ticker, shares, price, price]
        pass

    def long_portfolio(self, portfolio : pd.DataFrame):
        assert (self.position.columns == portfolio.columns).all()
        assert (self.position.loc[self.position['ticker'] == 'cash', 'shares'] >= portfolio['price'].dot(portfolio['shares'])).all()

        if portfolio['ticker'].isin(self.position.ticker.values).any():
            plus = portfolio.loc[portfolio['ticker'].isin(self.position.ticker.values)]
            # calculate total value of position
            total_value = (self.position.loc[self.position.ticker.isin(plus['ticker']).index, 'shares'] * 
                                        self.position.loc[self.position.ticker.isin(plus['ticker']).index, 'price'])
            total_value = total_value + (plus['shares'] * plus['price'])
            # plus new share
            self.position.loc[self.position['ticker'] == plus['ticker'], 'shares'] += plus['shares']
            # calculate average cost of position
            self.position.loc[self.position['ticker'] == plus['ticker'], 'price'] = (
                total_value / self.position.loc[self.position.ticker == plus['ticker'], 'shares'])

            portfolio = portfolio.loc[~portfolio['ticker'].isin(self.position.ticker.values)]
        
        if portfolio.shape[0] > 0:
            
            self.position = pd.concat([self.position, portfolio])
        
        self.position.loc[self.position['ticker'] == 'cash', 'shares'] -= portfolio['price'].dot(portfolio['shares'])

        return self.position
    
    def short(self, ticker, shares):
        if ticker in self.position.ticker.values:
            # minus new share
            self.position.loc[self.position.ticker == ticker, 'shares'] -= shares

            if self.position.loc[self.position.ticker == ticker, 'shares'] == 0:
                self.position = self.position.drop(ticker)
        
        else:
            raise Exception('no position')
        
        pass
    
    def short_portfolio(self, portfolio : pd.DataFrame):
        assert (self.position.columns == portfolio.columns).all()
        
        if portfolio['ticker'].isin(self.position.ticker.values).any():
            plus = portfolio.loc[portfolio['ticker'].isin(self.position.ticker.values)]
            # miuns new share
            position = self.position.set_index('ticker')
            position.loc[plus['ticker'], 'shares'] -= plus.set_index('ticker')['shares']

            portfolio = portfolio.loc[~portfolio['ticker'].isin(self.position.ticker.values)]

            # 删掉0股票
            self.position = position.reset_index()
            self.position = self.position.drop(self.position[self.position['shares'] == 0].index)

            #卖出加回cash
            self.position.loc[self.position['ticker'] == 'cash', 'shares'] += plus['price'].dot(plus['shares'])

        if portfolio.shape[0] > 0:
            
            raise Exception('no position')
        
        return self.position

    def trade_on_target_position(self, target_position : pd.DataFrame):
        assert (target_position.columns == self.position.columns).any()
        # assert target_position['ticker'].isin(self.position.ticker.values).all()

        diff = self.position.set_index('ticker').drop('cash').join(target_position.set_index('ticker'), how='outer', lsuffix='left_',
                                                      rsuffix='right_')
        diff = diff.fillna(0)
        diff['diff'] = diff['sharesright_'] - diff['sharesleft_']

        if (diff['diff'] > 0).any():
            self.long_portfolio(target_position.set_index('ticker').loc[diff['diff'] > 0, :].reset_index())

        if (diff['diff'] < 0).any():
            self.short_portfolio(target_position.set_index('ticker').loc[diff['diff'] < 0, :].reset_index())
        return self.position
    

