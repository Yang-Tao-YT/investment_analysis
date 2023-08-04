from strategy.option.宽跨 import StrangleOption
from data.database import _get_hs300_history_options, _get_hs300_history, _get_hs300_history_unadjust
from utils.calculate import calculate_call_margin, calculate_put_margin, calculate_mergin
import pandas as pd



def calcualte_returns_per_month(_portfolios : pd.Series, option_price, _trade_day, price):

    _price = price.loc[_trade_day]
    _portfolios = _portfolios.dropna()
    _portfolios = _portfolios.to_frame('shares').join(option_price)
    _portfolios = _portfolios.loc[_portfolios.index.get_level_values(0) >= _trade_day]
    # 计算最初value和保证金
    _portfolio = _portfolios.loc[_portfolios.index.get_level_values(0)[0]].copy()
    _portfolio = calculate_mergin(_portfolio, _price)
    _option_price = _portfolio['收盘价'].astype(float)
    combine_margin = max(_portfolio['保证金']) + min(_option_price)

    # print(_portfolio['执行价'].astype(float) / _price['收盘'])
    # print(_option_price, combine_margin)
    values = (_option_price * _portfolio['shares']).sum()
    cost = combine_margin

    # 最终value
    _portfolio = _portfolios.loc[_portfolios.index.get_level_values(0)[-1]].copy()
    _option_price = _portfolio['收盘价'].astype(float)
    values_end = (_option_price * _portfolio['shares']).sum()
    gain = values_end - values
    returns = gain / cost
    
    result = {}
    result['执行价格'] = _portfolio['执行价'].astype(float) / _price['收盘']
    result['return'] = returns
    result['option_price'] = _option_price
    result['combine_margin'] = combine_margin

    return result

def calcualte_returns(portfolio):
    price = _get_hs300_history_unadjust() ; price['前收盘'] = price['收盘'].shift() ; price.index = pd.to_datetime(price['日期'])
    option_price = _get_hs300_history_options(2022) ; option_price['日期'] = pd.to_datetime(option_price['日期'])
    option_price = option_price.set_index(['日期' , '合约编码'], drop=False)
    option_price['前收盘价'] = option_price['收盘价'].unstack().shift(1).stack()

    portfolio.index = pd.to_datetime(portfolio.index)

    records = {}
    for day in portfolio.index:
        records[day] = calcualte_returns_per_month(portfolio.loc[day], option_price, day, price)
        # print(calcualte_returns_per_month(portfolio.loc[day], option_price, day, price))
    return records

stra = StrangleOption()

option_price = _get_hs300_history_options(2022) ; option_price['日期'] = pd.to_datetime(option_price['日期'])
# option_price = option_price.set_index(['日期' , '合约编码'], drop=False)


portfolio = stra.generate_portfolios(data=option_price,)
# portfolio = {pd.to_datetime(k) : v for k,v in portfolio.items()}
portfolio = pd.concat(portfolio) 
portfolio = portfolio.direction.unstack()
if isinstance(portfolio, pd.Series) : 
    portfolio = portfolio.to_frame() 


results = calcualte_returns(portfolio)
test = pd.DataFrame(results).T
test[['执行价格', 'return']]
# results[0]
turnover_days = portfolio.index
_trade_day  = pd.to_datetime('2022-01-06')
_trade_day  = pd.to_datetime('2022-01-05')
values_record = []
portfolio_records = []
option_price = option_price.set_index(['日期' , '合约编码'], drop=False)
for _trade_day in turnover_days:
        _portfolio = portfolio.loc[_trade_day]
        _option_price = option_price.loc[_trade_day]
        _price = price.loc[_trade_day]

        _option_price
        _portfolio = _portfolio.dropna()
        _portfolio = _portfolio.to_frame('shares').join(_option_price)
        

        _portfolio = calculate_mergin(_portfolio, _price)
        _option_price = _portfolio['收盘价'].astype(float)
        _portfolio['标的收盘价']
        combine_margin = max(_portfolio['保证金']) + min(_option_price)

        values = (_option_price * _portfolio['shares']).sum()
        cost = combine_margin
        gain = 0
        returns = gain / cost
        values_record += [{'date' : _trade_day, 'cost' : cost, 'values' : values, 'returns' : returns}]
        portfolio_records +=[ _portfolio[['shares']]]



    




