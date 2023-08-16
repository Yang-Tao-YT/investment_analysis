import copy
import pandas as pd
from utils.basic import name_2_symbol, rename_dataframe, Bar, send_to
from stock_strategy import StockIndex, stock_etf_hist_dataloader
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
        if setting is not None:
            self.update_setting(setting=setting)

        if preset_close is not None:
            self.stock_index.am.close_array[-1] = preset_close
            self.stock_index.origin_data.loc[self.stock_index.origin_data.index[-1] , 'close'] = preset_close

        indicator = return_indicator(indicator=indicator, stockindex_copy = self.stock_index)
        return indicator
    
def return_stockindex(symbol, setting : dict = None):
    '''下载历史数据'''
    stockindex = StockIndex()
    hist = stock_etf_hist_dataloader(symbol)
    hist = rename_dataframe(hist)
    hist['date'] = pd.to_datetime(hist['date']).dt.date
    #转换成stockindex的形式
    stockindex.set_am(hist)
    setattr(stockindex, 'origin_data', hist.set_index('date')) 
    # update setting
    if setting is not None:
        stockindex.update_setting(setting=setting)
    return stockindex

def return_indicator(indicator, stockindex_copy = None):
    if len(indicator) > 0:
        result = {}
        for i in indicator:
             _temp = eval(f'stockindex_copy.{i}().iloc[:, :]')
             _temp = _temp.set_index(0)
             result[i] = _temp.squeeze()
        
        
        return pd.concat(result, axis = 1)
    return eval(f'stockindex_copy.{indicator[0]}().iloc[-20:, :]')

def calculate_indicator(symbol, indicator = ['risk'], setting=None, preset_close = None):
    stockindex = return_stockindex(symbol, setting=setting)
    stockindex_copy = copy.deepcopy(stockindex)
    stockindex_copy.origin_data['pre_close'] = stockindex_copy.origin_data.close.shift(1)
    bar = Bar().update_bar(stockindex_copy.origin_data.iloc[-1,:])

            
    if preset_close is not None:
        stockindex_copy.am.close_array[-1] = preset_close
        stockindex_copy.origin_data.loc[stockindex_copy.origin_data.index[-1] , 'close'] = preset_close

    result = return_indicator(indicator=indicator, stockindex_copy = stockindex_copy)

    #检查联系日期
    continue_date = find_continue_date(list(
        (result[_ix]['indicator'].loc[(result[_ix]['indicator'] < result[_ix]['indicator'].iloc[-1]).squeeze()].index)
    ))

    #检查risk是否连续下降
    result[_ix]['indicator'].index = pd.to_datetime(result[_ix]['indicator'].index)
    for k, _continue in enumerate(continue_date) :
        _data = result[_ix]['indicator'].loc[_continue]
        if _data.shape[0] > 1:
            #判断是否下降
            _diff : pd.DataFrame
            _diff = _data.diff() < 0
            _diff.iloc[0] = True
            if (~_diff).any().squeeze():
                _data = _data[ _data.index < _diff.replace(True, value = None).first_valid_index()]
                continue_date[k] = list(_data.index)

    #计算平均日长
    np.mean([len(i) for i in continue_date])
    np.median([len(i) for i in continue_date])

    for k, _continue in enumerate(continue_date) :
        _data = result[_ix]['indicator'].loc[_continue]
        _date = _data.index[0]


    return {'indicator' : result, 'bar' : bar}

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
            

def main(if_save = True, setting = None) -> Results:
    # 挨个计算 bar 和 indicator
    result = {}
    for _ix in list( name_2_symbol.keys()):
        result[_ix] =  calculate_indicator(name_2_symbol[_ix], setting = setting)
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