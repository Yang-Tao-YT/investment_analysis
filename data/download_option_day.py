from .genenrate_data import DataLoader
import pandas as pd


def download():
    loader =  DataLoader()
    data = loader.current_em()
    hs300 = loader.current_hs300sz_em()

    data = pd.concat([data, hs300])
    data = data.set_index('代码')
    data = data.apply(pd.to_numeric,args=['ignore'])

    # greek
    greek = loader.current_risk_em()

    hs300 = loader.current_hs300risk_sz_em()
    greek = pd.concat([greek, hs300])
    greek = greek.set_index('期权代码')
    greek = greek.apply(pd.to_numeric,args=['ignore'])

    return data, greek
