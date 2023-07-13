'''
backtesting 框架'''
import pandas as pd



class Statistic(object):
    kdata:pd.DataFrame
    def __init__(self):
        pass

    def statistic(self,data):
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

    def generate_signal(self):
        """
        The function `generate_signal` generates a signal DataFrame.
        
        Args:
          signal (pd.DataFrame): signal is a pandas DataFrame containing signal data. It has the
        following columns:
        """
        return 'signal'