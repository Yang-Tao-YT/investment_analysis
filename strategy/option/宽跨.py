from data.database import _get_hs300_history_options
import pandas as pd
from .option_strategy import Strategy

class StrangleOption(Strategy):

    def process_conctracts(self, contracts):
        contracts = contracts.rename(columns = {'行权价' : '执行价'})
        if '期权类型' not in contracts.columns:
            contracts['期权类型'] = None
            contracts.loc[contracts.名称.str.contains('购'), '期权类型'] = 'C'
            contracts.loc[contracts.名称.str.contains('沽'), '期权类型'] = 'P'
        
        if '合约编码' not in contracts.columns:
            contracts['合约编码'] = contracts.index

        return contracts

    def chose_contract(self, contracts, current_price = None, std = 0.075,  round_type = 'down'):

        # var
        # current_price = 4.99 ; std = 0.075; contracts = test; round_type  = 'down'
        contracts = self.process_conctracts(contracts)

        current_price
        if current_price is None:
            current_price = float(contracts.标的收盘价.iloc[0])
        up = round(current_price * (1 + std), 2)
        down = round(current_price * (1 - std), 2)

        if round_type == 'down' :
            contracts.loc[(contracts.期权类型 == 'C')]
            up = contracts.loc[(contracts.执行价.astype(float) >= up) & 
                            (contracts.期权类型 == 'C')].sort_values('执行价')['合约编码'].iloc[0]
            
            contracts.loc[(contracts.期权类型 == 'P')]
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
        """
        The function `generate_portfolios` generates portfolios of call and put options based on historical
        data, with the option to specify a target standard deviation and rounding type.
        
        Args:
          data: The `data` parameter is a pandas DataFrame that contains historical data for options
        contracts. If no `data` is provided, the function will try to retrieve historical data for the HS300
        index options for the specified `year`.
          year: The `year` parameter is used to specify the year for which the portfolios need to be
        generated. If the `data` parameter is not provided, the function will use the
        `_get_hs300_history_options()` function to fetch the historical data for the specified year.
          std: The `std` parameter in the `generate_portfolios` function represents the standard deviation.
        It is used as a threshold value for selecting contracts. 
          round_type: The `round_type` parameter determines how the calculated values will be rounded. It
        can take two values:. Defaults to down
        
        Returns:
          a dictionary named "result".
        """
        if data is None:
            if year is None:
                raise Exception('year and data cannot be None')
                return
            
            data = _get_hs300_history_options(year)
        data = data.loc[data.日期 != data.日期.iloc[0]]

        contract_date = data.loc[pd.DatetimeIndex(data.日期).month == pd.DatetimeIndex(data.到期日).month]
        contract_date['day'] = pd.DatetimeIndex(contract_date.日期).day
        contract_date['month'] = pd.DatetimeIndex(contract_date.日期).month

        contract_date = contract_date.join(contract_date.groupby('month')['day'].min(),rsuffix = 'first_', on = 'month')
        contract_date = contract_date.loc[contract_date['dayfirst_'] == contract_date['day']]
        result = {}
        for i in contract_date.groupby('日期'):
            print(i[0])
            call, down = self.chose_contract(i[1], std = std, round_type=round_type)
            _result = pd.concat([call, down]).set_index('合约编码')[['期权类型']]
            _result['direction'] = -1

            result[i[0]] = _result


        return result
    

    




