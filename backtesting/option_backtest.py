from strategy.宽跨 import StrangleOption
from data.database import _get_hs300_history_options, _get_hs300_history
from utils.calculate import calculate_call_margin, calculate_put_margin
import pandas as pd

stra = StrangleOption()
option_price = _get_hs300_history_options(2022)
price = _get_hs300_history() ; price['前收盘'] = price['收盘'].shift() ; price.index = pd.to_datetime(price['日期'])

portfolio = stra.generate_portfolios(data=option_price,)
portfolio = pd.concat(portfolio)
portfolio = portfolio.unstack()

portfolio.loc['20220104']

turnover_days = pd.to_datetime(portfolio.index)
trading_days = pd.to_datetime(price.index)
trading_days[]




