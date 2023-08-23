import pandas as pd
import os
from data.generate_data import DataLoader
import option_strategy
from strategy.stock_strategy import return_stockindex, return_indicator


def load_position(axis = 1):
    # dataframe = pd.read_csv('position.csv', encoding = 'utf-8-sig', index_col=0)
    # dataframe = dataframe.replace({'义务' : -1, '权利' : 1})
    # dataframe = dataframe.set_index('合约代码')
    # dataframe1 = dataframe.loc[~dataframe.index.isna()].copy()

    dataframe1 = pd.DataFrame()
    if os.path.exists('huataiposition.csv'):
        try:
            dataframe = pd.read_csv('huataiposition.csv', index_col=0)
        except:
            dataframe = pd.read_csv('huataiposition.csv', index_col=0, encoding='gbk')

        dataframe = dataframe.dropna(axis=1)
        def trans(x:str):
            if isinstance(x, str):
                x = x.strip('=')
                x = x.strip('"')
            return x
        dataframe = dataframe.applymap(trans)
        dataframe = dataframe.replace({'义务' : -1, '权利' : 1, })
        dataframe = dataframe.rename(columns={'定价' : '定价价栳n','开仓均价' :'成本价',
                                    '净仓' : '实际持仓'})
        dataframe = dataframe.astype({'成本价' : float, '实际持仓' : int,})

        dataframe['持仓类型'] = 1 ; dataframe.loc[dataframe['实际持仓'] < 0 , '持仓类型'] = -1
        dataframe['实际持仓'] = abs(dataframe['实际持仓'])

        dataframe = dataframe.set_index('合约编码')
        dataframe = dataframe.loc[~dataframe.index.isna()]

        dataframe1 = pd.concat([dataframe1, dataframe], axis = 0).sort_index()

        dataframe1.index = dataframe1.index.astype(str)
    return dataframe1

def return_account():
    loader =  DataLoader()
    trad = option_strategy.Trading()
    dataframe = load_position(1)
    dataframe['under'] = dataframe.合约名称.str[:6]
    data = loader.current_em()
    hs300 = loader.current_hs300sz_em()

    data = pd.concat([data, hs300])
    data = data.set_index('代码')
    data = data.apply(pd.to_numeric,args=['ignore'])

    # greek
    greek = loader.current_risk_em()
    # hs300 = loader.current_hs300risk_sz_em()
    # greek = pd.concat([greek, hs300])
    greek = greek.set_index('期权代码')
    greek = greek.apply(pd.to_numeric,args=['ignore'])


    trad.update_bar(data)
    trad.update_greek(greek)
    
    trad.load_position(dataframe)
    profit = trad.profit()

    trad.update_position()

    # get price of underlying asset
    hs300_price = return_stockindex('sh510300', None).origin_data.iloc[-1,:]['close']
    zz500_price = return_stockindex('sh510500', None).origin_data.iloc[-1,:]['close']
    shs300_price = return_stockindex('sz159919', None).origin_data.iloc[-1,:]['close']
    # calculate scale
    test = trad.position.iloc[:-1].copy()
    test.loc[test.合约名称.str.contains('510300'), '行权价'] = test.loc[test.合约名称.str.contains('510300') , '行权价'] / hs300_price - 1
    test.loc[test.合约名称.str.contains('159919') , '行权价'] = test.loc[ test.合约名称.str.contains('159919') , '行权价'] / shs300_price - 1
    
    test.loc[test.合约名称.str.contains('500ETF')| test.合约名称.str.contains('510500') , '行权价'] = test.loc[test.合约名称.str.contains('500ETF')| test.合约名称.str.contains('510500') , '行权价'] / zz500_price - 1
    trad.position.insert(4, '比例', list((test['行权价'] * 100).values) + [None]) 
    trad.position.insert(4, '比例绝对值', list(abs(test['行权价'] * 100).values) + [None]) 

    return trad