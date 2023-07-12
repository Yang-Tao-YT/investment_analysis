'''
backtesting 框架'''
import pandas as pd

class _BacktestUtils:
    position = pd.DataFrame(columns=['ticker', 'shares', 'price', 'cost'])

    def calculate_position_value(self):
        return self.position['shares'].dot(self.position['cost'])
    
class Backtest(_BacktestUtils):

    start_date = ''
    end_date = ''
    kdata = pd.DataFrame()
    position = pd.DataFrame(columns=['ticker', 'shares', 'price', 'cost'])
    initial_account = 0
    cash = 0
    total_value = 0
    total_profit = 0
    total_value_record = {}
    total_profit_record = {}

    def __init__(self) -> None:
        pass
    
    def load_data(self, kdata : pd.DataFrame):
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
        if config is not None:
            for key in config:
                setattr(self, key, config[key])

    def on_bar(self, date, data):
        pass

    def run(self):

        data = self.kdata
        index = data['date'][(data['date'] >= self.start_date) & (data['date'] <= self.end_date)]
        data = data.sort_values(by=['date'])
        # inital position
        self.position.loc[0] = ['cash' ,self.initial_account, 1, 1]

        self.total_value = self.calculate_position_value()

        for _index in index:
            on_bar_data = data.loc[data['date'] <= _index]
            self.on_bar(_index, on_bar_data)
            self.total_value = self.calculate_position_value()

            pass

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
        assert self.position.columns == portfolio.columns
        
        if portfolio['ticker'].isin(self.position.ticker.values).any():
            plus = portfolio.loc[portfolio['ticker'].isin(self.position.ticker.values)]
            # calculate total value of position
            total_value = (self.position.loc[self.position.ticker == plus['ticker'], 'shares'] * 
                                        self.position.loc[self.position.ticker == plus['ticker'], 'price'])
            total_value = total_value + (plus['shares'] * plus['price'])
            # plus new share
            self.position.loc[self.position['ticker'] == plus['ticker'], 'shares'] += plus['shares']
            # calculate average cost of position
            self.position.loc[self.position['ticker'] == plus['ticker'], 'price'] = (
                total_value / self.position.loc[self.position.ticker == plus['ticker'], 'shares'])

            portfolio = portfolio.loc[~portfolio['ticker'].isin(self.position.ticker.values)]
        
        if portfolio.shape[0] > 0:
            
            self.position = pd.concat([self.position, portfolio])

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
        assert self.position.columns == portfolio.columns
        
        if portfolio['ticker'].isin(self.position.ticker.values).any():
            plus = portfolio.loc[portfolio['ticker'].isin(self.position.ticker.values)]
            # miuns new share
            self.position.loc[self.position['ticker'] == plus['ticker'], 'shares'] -= plus['shares']
            
            portfolio = portfolio.loc[~portfolio['ticker'].isin(self.position.ticker.values)]
        
        if portfolio.shape[0] > 0:
            
            raise Exception('no position')
        
        return self.position


    def trade_on_target_position(self, target_position : pd.DataFrame):
        assert target_position.columns == self.position.columns
        # assert target_position['ticker'].isin(self.position.ticker.values).all()

        diff = self.position.set_index('ticker').join(target_position.set_index('ticker'), how='outer', lsuffix='left_',
                                                      rsuffix='right_')
        diff = diff.fillna(0)
        diff['diff'] = diff['left_shares'] - diff['right_shares']
        self.long_portfolio(diff.loc[diff['diff'] > 0, :])
        self.short_portfolio(diff.loc[diff['diff'] < 0, :])
        return self.position
    

