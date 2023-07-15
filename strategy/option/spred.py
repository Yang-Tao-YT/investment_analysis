import numpy as np
import pandas as pd
from .option_strategy import Strategy


class Spred(Strategy):

    def process_conctracts(self, contracts):
        contracts = contracts.rename(columns = {'行权价' : '执行价'})
        if '期权类型' not in contracts.columns:
            contracts['期权类型'] = None
            contracts.loc[contracts.名称.str.contains('购'), '期权类型'] = 'C'
            contracts.loc[contracts.名称.str.contains('沽'), '期权类型'] = 'P'
        
        if '合约编码' not in contracts.columns:
            contracts['合约编码'] = contracts.index

        return contracts
    
    def bullspread_call(K1,K2,C1,C2,P0,P0_index,Pt_index,N1,N2,N_underlying):
        '''K1:较低期权的执行价格；
        K2:较高期权的执行价格；
        C1:较低执行价格期权的当前价格；
        C2:较高执行价格期权的当前价格；
        P0:标的资产当前单位净值价格；
        P0_index：标的资产当前收盘点位；
        Pt_index：期权到期日标的资产收盘点位；
        N1:较低执行价格的期权多头头寸数量；
        N2:较高执行价格的期权多头头寸数量；
        N_underlying：1张标的资产期权基础资产是多少份单位净值.'''    
        Pt=P0*Pt_index/P0_index  #期权到期日标的资产基金净值数组
        call_long=N1*N_underlying*(np.maximum(Pt-K1,0)-C1) #期权到期日较低执行价格期权多头头寸的盈亏
        call_short=N2*N_underlying*(C2-np.maximum(Pt-K2,0)) #期权到期日较高执行价格期权空头头寸的盈亏
        bull_spread=call_long+call_short
        return Pt_index,call_long,call_short,bull_spread  #期权到期日牛市价差盈亏
    

    def chose_contract(self, contracts, current_price = None, std = 0.075,  round_type = 'down'):

        # var
        # current_price = 4.99 ; 
        std = 0.025; 
        # contracts = test; round_type  = 'down'
        contracts = self.process_conctracts(contracts)

        if current_price is None:
            current_price = float(contracts.标的收盘价.iloc[0])

        up = round(current_price, 2)
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