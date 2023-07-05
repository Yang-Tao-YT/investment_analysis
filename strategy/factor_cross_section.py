import copy
import pandas as pd
from utils.basic import name_2_symbol, rename_dataframe, Bar
from stock_strategy import StockIndex, stock_etf_hist_dataloader

class Results:
    indicator = None
    bar = None

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

def calculate_indicator(symbol, indicator = ['risk'], setting=None):
    stockindex = return_stockindex(symbol, setting=setting)
    stockindex_copy = copy.deepcopy(stockindex)
    stockindex_copy.origin_data['pre_close'] = stockindex_copy.origin_data.close.shift(1)
    bar = Bar().update_bar(stockindex_copy.origin_data.iloc[-1,:])
    result = return_indicator(indicator=indicator, stockindex_copy = stockindex_copy)

    return {'indicator' : result, 'bar' : bar}

def main(if_save = True) -> Results:
    # 挨个计算 bar 和 indicator
    result = {}
    for _ix in list( name_2_symbol.keys()):
        result[_ix] =  calculate_indicator(name_2_symbol[_ix])
        print(result[_ix])


    #整合
    indicator = {k: v['indicator'].iloc[-1].squeeze() for k, v in result.items()}
    bar = {k:str(round(v['bar'].close/v['bar'].pre_close - 1, 3)* 100) + '%' for k, v in result.items()}
    results = Results() ; results.indicator = indicator; results.bar = bar

    #保存indicator
    indicator = pd.Series(indicator)
    if if_save:    
        import datetime
        indicator.to_csv(f'/usr/local/app/app/app/finance_data/etf_risk/{datetime.datetime.today().strftime("%Y%m%d")}')

    return results

if __name__ == '__main__':
    
    main(if_save=False)