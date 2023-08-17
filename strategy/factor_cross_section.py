import copy
import pandas as pd
from utils.basic import name_2_symbol, rename_dataframe, Bar, send_to
from strategy.stock_strategy import StockIndex, return_stockindex, return_indicator
import numpy as np

class Results:
    indicator = None
    bar = None
    quantile = None
    percent = None
    last_indicator = None

    def set_attr(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)


class FCS:
    stock_index : StockIndex = None

    def __init__(self) -> None:
        pass
    
    def clean(self):
        self.stock_index = None

    def update_setting(self, setting : dict = None):
        for k,v in setting.items():
            setattr(self, k, v)

    def obtain_current_stockindex(self, symbol, setting : dict = None):
        '''获取完故的stockindex'''
        if self.stock_index is None:
            self.stock_index = return_stockindex(symbol, setting=setting)
        return self.stock_index
    
    def obtain_current_indicator(self,  indicator = ['risk'], setting=None, preset_close = None):
        """
        The function `obtain_current_indicator` returns the specified indicator value based on the given
        settings and preset close value.
        
        Args:
          indicator: The indicator parameter is a list that specifies which indicators to obtain. The
        default value is ['risk'], which means it will obtain the risk indicator. However, you can pass in
        other indicators as well.
          setting: The `setting` parameter is used to update the settings of the coding assistant. It is an
        optional parameter and can be used to modify any settings that affect the behavior of the coding
        assistant.
          preset_close: The parameter "preset_close" is used to set a specific closing price for the stock.
        This is useful when you want to calculate the risk indicator based on a specific closing price
        instead of the actual closing price of the stock.
        
        Returns:
          the calculated indicator value.
        """
        if setting is not None:
            self.update_setting(setting=setting)

        if preset_close is not None:
            #根据设定好的preset_close 计算risk
            self.stock_index.am.close_array[-1] = preset_close
            self.stock_index.origin_data.loc[self.stock_index.origin_data.index[-1] , 'close'] = preset_close

        indicator = return_indicator(indicator=indicator, stockindex = self.stock_index)
        return indicator
    
def calculate_indicator(symbol, 
                        indicator = ['risk'], 
                        setting=None, 
                        preset_close = None, 
                        end_date = None,
                        if_analysis_down_risk = False,
                        if_analysis_risk_after_first_comback = False):
    stockindex = return_stockindex(symbol, setting=setting, end_date = end_date)
    stockindex_copy = copy.deepcopy(stockindex)
    stockindex_copy.origin_data['pre_close'] = stockindex_copy.origin_data.close.shift(1)
    bar = Bar().update_bar(stockindex_copy.origin_data.iloc[-1,:])


    if preset_close is not None:
        stockindex_copy.am.close_array[-1] = preset_close
        stockindex_copy.origin_data.loc[stockindex_copy.origin_data.index[-1] , 'close'] = preset_close

    result = return_indicator(indicator=indicator, stockindex = stockindex_copy)

    if if_analysis_down_risk:
        down_risk_analysis = find_down_risk_at_current_risk(result, stockindex_copy.origin_data['close'])

    if if_analysis_risk_after_first_comback:
        analysis = find_down_risk_after_first_comback(result, stockindex_copy.origin_data['close'])
    # up_risk_analysis = find_up_risk_at_current_risk(result, stockindex_copy.origin_data['close'])

    return {'indicator' : result, 'bar' : bar}

def find_risk_trend(date, indicator):
    records = [date]
    now = indicator.loc[date].squeeze()
    _indicator = indicator.loc[indicator.index > date ].squeeze()
    for _indi in _indicator.index:
        if _indicator[_indi] > now:
            break
        else:
            records += [_indi]
            now = _indicator[_indi]
    return records

def find_down_risk_at_current_risk(indicator, close):
    indicator.index = pd.to_datetime(indicator.index)
    close.index = pd.to_datetime(close.index)
    result = indicator.copy()
    
    #找进口
    indicator['t+1'] = indicator.shift(-1)
    indicator['t+1day'] = list(pd.Series(indicator.index).shift(-1))
    enter = indicator.loc[(indicator['risk'] >= indicator['risk'][-1]) & (indicator['t+1'] < indicator['risk'][-1])]

    indicator.loc[(indicator['risk'] < indicator['risk'][-1])]
    #根据近值选择
    def chose(df):
        if df['close'] == 't+1':
            return df['t+1day']
        elif df['close'] == 'risk':
            return df.name

    enter = list(enter.join((enter[['risk', 't+1']] - indicator['risk'][-1]).abs().idxmin(axis = 1).to_frame('close')).apply(chose, axis = 1))

    continue_date = []
    for _enter in enter:
        continue_date += [find_risk_trend(_enter, result)]
    
    #计算平均日长
    mean_day = np.mean([len(i) -1 for i in continue_date])
    median_day = np.median([len(i) -1 for i in continue_date])

    #计算次数
    count = len(continue_date)

    #计算t+1收益
    returns_1 = close.pct_change().shift(-1)
    returns_1.index = pd.to_datetime(returns_1.index)
    _returns_1 = pd.Series()
    for k, _continue in enumerate(continue_date):
        close.loc[_continue]
        _data = result.loc[_continue]
        _date = _data.index[0]
        returns = returns_1.loc[pd.to_datetime(_date)]
        _returns_1.loc[_date] = returns


    #计算t收益
    returns_ = close.pct_change()
    returns_.index = pd.to_datetime(returns_.index)
    _returns_ = pd.Series()
    for k, _continue in enumerate(continue_date) :
        _data = result.loc[_continue]
        _date = _data.index[0]
        returns = returns_.loc[_date]
        _returns_.loc[_date] = returns

    #计算t+5收益
    _return_p_5 = pd.Series()
    for k, _continue in enumerate(continue_date) :
        _date = _continue[0]
        _close = close.loc[ _date: ].iloc[:6]
        _return_p_5.loc[_date] = _close.iloc[-1] / _close.iloc[0] - 1

    return pd.Series({'平均日长' : mean_day,
            '中位数日长' : median_day,
            't+1收益' : _returns_1.mean(),
            't+1收益中位数' : _returns_1.mean(),
            't收益' : _returns_.mean(),
            't收益中位数' : _returns_.mean(),
            '次数' : count,
            '当天占比' : sum([1 for _continue in continue_date if len(_continue) == 1 ] ) / count,
            '1t占比' : sum([1 for _continue in continue_date if len(_continue) == 2 ] ) / count,
            '1t下跌平均' : _returns_1.loc[_returns_1 < 0].mean(),
            '1t下跌中位数' : _returns_1.loc[_returns_1 < 0].median(),            
            '未来5日平均' : _return_p_5.mean(),
            '未来5日中位数' : _return_p_5.median()})


def find_down_risk_after_first_comback(indicator, close, compare_indicator = None, special_returns = None):
    indicator.index = pd.to_datetime(indicator.index)
    close.index = pd.to_datetime(close.index)

    if compare_indicator is None:
        compare_indicator = indicator['risk'].iloc[-1]


    result = indicator.copy()
    # 计算第二天变化值
    indicator['t+1'] = indicator.shift(-1)
    indicator['diff+1'] = indicator['t+1'] - indicator['risk']

    # 找出比目标indicator低同时第二天反弹的日期
    _date = indicator.loc[(indicator['risk'] < 15) & (indicator['diff+1'] > 0)].index

    # 计算收益
    returns = close.pct_change().to_frame('returns')
    for _t in range(1,7):
        returns[f't+{_t}'] = returns['returns'].shift(-_t)

    # 找出收益
    res_returns = returns.loc[_date]


    #计算t+1收益
    mean_1 = res_returns['t+1'].mean()
    median_1 =res_returns['t+1'].median()

    #计算t+2收益
    mean_2 = res_returns['t+2'].mean()
    median_2 = res_returns['t+2'].median()

    records = {'t+1收益' : mean_1,
            't+1收益中位数' : median_1,
            't+2收益' : mean_2,
            't+2收益中位数' : median_2,}
    if special_returns is not None:
        _sr_indicator = indicator.loc[_date].join(res_returns, lsuffix = '_ind').loc[res_returns['t+1'] < 0.003]
        records['特殊t+1收益率下t+2收益'] = _sr_indicator['t+2'].mean()
        records['特殊t+1收益率下t+2收益中位数'] = _sr_indicator['t+2'].median()

    return pd.Series(records)

def find_continue_date(date):
    import exchange_calendars as xcals
    XSHG = xcals.get_calendar('XSHG', start='2010-12-19')
    td = XSHG.schedule.index
    trade_date_sse = pd.to_datetime([i for i in td])
    records = []
    _re = []

    while len(date) > 0:
        # _re = []
        _date = date.pop(0)
        _date = pd.to_datetime(_date)

        #如果记录为空，记录头
        if len(_re) == 0:
            # if _date in trade_date_sse:
            _re += [_date]
        else:
            #否则判断是否连续
            n_day = trade_date_sse [trade_date_sse > _re[-1]][0]
            if _date == n_day:
                _re += [_date]
            
            else:
                records += [_re]
                _re = [_date]

        if len(date) == 0:
            records += [_re]

    return records
            

def main(if_save = True, setting = None, end_date = None) -> Results:
    # 挨个计算 bar 和 indicator
    result = {}
    for _ix in list( name_2_symbol.keys()):
        result[_ix] =  calculate_indicator(name_2_symbol[_ix], setting = setting, end_date = end_date)
        result[_ix]['quantile'] = (result[_ix]['indicator'] < result[_ix]['indicator'].iloc[-1]).sum() / result[_ix]['indicator'].shape[0]
        
        print(result[_ix])


    #整合
    indicator = {k: v['indicator'].iloc[-1].squeeze() for k, v in result.items()}
    last_indicator = {k: v['indicator'].iloc[-2].squeeze() for k, v in result.items()}
    percent = {k:v['bar'].close/v['bar'].pre_close *1 - 1  for k, v in result.items()}
    quantile = {k: v['quantile'].squeeze() for k, v in result.items()}

    results = Results() 
    results.indicator = indicator
    results.percent = percent
    results.quantile = quantile
    results.bar = {k:v['bar'].close for k, v in result.items()}
    results.last_indicator = last_indicator
    #保存indicator
    indicator = pd.Series(indicator)
    
    if if_save:    
        import datetime
        indicator.sort_values().to_csv(f'../finance_data/etf_risk/{datetime.datetime.today().strftime("%Y%m%d")}.csv')
        send_to(Subject='hi, yang',
                messages=pd.read_csv(f'../finance_data/etf_risk/{datetime.datetime.today().strftime("%Y%m%d")}.csv').to_string()
                 ,attach=f'../finance_data/etf_risk/{datetime.datetime.today().strftime("%Y%m%d")}.csv')
        
    return results

if __name__ == '__main__':
    
    main(if_save=False)