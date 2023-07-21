import copy
import pandas as pd
from utils.basic import name_2_symbol, rename_dataframe, Bar, send_to
from stock_strategy import StockIndex, stock_etf_hist_dataloader

class Results:
    indicator = None
    bar = None
    quantile = None
    percent = None

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

    return {'indicator' : result, 'bar' : bar}

def main(if_save = True, setting = None) -> Results:
    # 挨个计算 bar 和 indicator
    result = {}
    for _ix in list( name_2_symbol.keys()):
        result[_ix] =  calculate_indicator(name_2_symbol[_ix], setting = setting)
        result[_ix]['quantile'] = (result[_ix]['indicator'] < result[_ix]['indicator'].iloc[-1]).sum() / result[_ix]['indicator'].shape[0]
        print(result[_ix])


    #整合
    indicator = {k: v['indicator'].iloc[-1].squeeze() for k, v in result.items()}
    percent = {k:v['bar'].close/v['bar'].pre_close *1 - 1  for k, v in result.items()}
    quantile = {k: v['quantile'].squeeze() for k, v in result.items()}

    results = Results() ; 
    results.indicator = indicator; 
    results.percent = percent
    results.quantile = quantile
    results.bar = {k:v['bar'].close for k, v in result.items()}
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