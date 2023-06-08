from data.database import _get_hs300_history_options
import pandas as pd
from .strategy import Strategy

class StrangleOption(Strategy):
    def chose_contract(self, contracts, current_price = None, std = 0.075,  round_type = 'down'):

        # var
        # current_price = 4.99 ; std = 0.075; contracts = test; round_type  = 'down'
        if current_price is None:
            current_price = float(contracts.标的收盘价.iloc[0])
        up = round(current_price * (1 + std), 2)
        down = round(current_price * (1 - std), 2)

        if round_type == 'down' :
            up = contracts.loc[(contracts.执行价.astype(float) >= up) & 
                            (contracts.期权类型 == 'C')].sort_values('执行价')['合约编码'].iloc[0]
            
            down = contracts.loc[(contracts.执行价.astype(float) <= down) & 
                                (contracts.期权类型 == 'P')].sort_values('执行价')['合约编码']
            if down.shape[0] == 1:
                down = down.iloc[0]
            else:
                down = down.iloc[1]

        elif round_type == 'up':        
            up = contracts.loc[(contracts.执行价.astype(float) <= up) & 
                        (contracts.期权类型 == 'C')].sort_values('执行价')['合约编码'].iloc[-1]
            down = contracts.loc[(contracts.执行价.astype(float) >= down) & 
                                (contracts.期权类型 == 'P')].sort_values('执行价')['合约编码'].iloc[0]

        up = contracts.loc[contracts.合约编码 == up]
        down = contracts.loc[contracts.合约编码 == down]
        # upprice = up['收盘价']
        # downprice = down['收盘价']
        return (up,down)

    def generate_portfolios(self,  data = None, year = None, std = 0.075,  round_type = 'down'):
        if data is None:
            if year is None:
                Warning('year and data cannot be None')
                return
            
            data = _get_hs300_history_options(year)

        contract_date = data.loc[pd.DatetimeIndex(data.日期).month == pd.DatetimeIndex(data.到期日).month]
        contract_date['day'] = pd.DatetimeIndex(contract_date.日期).day
        contract_date['month'] = pd.DatetimeIndex(contract_date.日期).month

        contract_date = contract_date.join(contract_date.groupby('month')['day'].min(),rsuffix = 'first_', on = 'month')
        contract_date = contract_date.loc[contract_date['dayfirst_'] == contract_date['day']]
        result = {}
        for i in contract_date.groupby('日期'):
            print(i[0])
            call, down = self.chose_contract(i[1], std = std, round_type=round_type)

            result[i[0]] = pd.Series([call.合约编码.squeeze(), down.合约编码.squeeze()], index = ['call', 'put'])


        return result




