from gridtrading.Backtest.snowball_backtest import snowball_backtest
from data.generate_data import DataLoader

dl = DataLoader()
kdata = dl.stock_etf_hist_dataloader(symbol='sh000905')

snowball_backtest(kdata)