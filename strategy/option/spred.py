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
    
    @staticmethod
    def bullspread_call(K1,K2,C1,C2,P0,P0_index,Pt_index,N1,N2,N_underlying):
        '''
        K1:较低期权的执行价格；
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

    @staticmethod
    def bearspread_call(K1,K2,C1,C2,P0,P0_index,Pt_index,N1,N2,N_underlying):
        '''
        K1:较低期权的执行价格；
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
        call_long=-1 * N1*N_underlying*(np.maximum(Pt-K1,0)-C1) #期权到期日较低执行价格期权多头头寸的盈亏
        call_short=-1 * N2*N_underlying*(C2-np.maximum(Pt-K2,0)) #期权到期日较高执行价格期权空头头寸的盈亏
        bull_spread=call_long+call_short
        return Pt_index,call_long,call_short,bull_spread  #期权到期日牛市价差盈亏 

    @staticmethod
    def bearspread_put(K1,K2,P1,P2,P0,P0_index,Pt_index,N1,N2,N_underlying):
        '''K1:较低期权的执行价格；
        K2:较高期权的执行价格；
        P1:较低执行价格期权的当前价格；
        P2:较高执行价格期权的当前价格；
        P0:标的资产当前单位净值价格；
        P0_index：标的资产当前收盘点位；
        Pt_index：期权到期日标的资产收盘点位；
        N1:较低执行价格的期权多头头寸数量；
        N2:较高执行价格的期权多头头寸数量；
        N_underlying：1张标的资产期权基础资产是多少份单位净值.'''    
        Pt=P0*Pt_index/P0_index  #期权到期日标的资产基金净值数组
        put_long=-1 * N1*N_underlying*(np.maximum(K1-Pt,0)-P1) #期权到期日较低执行价格期权多头头寸的盈亏
        put_short=-1 * N2*N_underlying*(P2-np.maximum(K2-Pt,0)) #期权到期日较高执行价格期权空头头寸的盈亏
        bull_spread=put_long+put_short
        return Pt_index,put_long,put_short,bull_spread  #期权到期日牛市价差盈亏

    
    @staticmethod
    def bullspread_put(K1,K2,P1,P2,P0,P0_index,Pt_index,N1,N2,N_underlying):
        '''K1:较低期权的执行价格；
        K2:较高期权的执行价格；
        P1:较低执行价格期权的当前价格；
        P2:较高执行价格期权的当前价格；
        P0:标的资产当前单位净值价格；
        P0_index：标的资产当前收盘点位；
        Pt_index：期权到期日标的资产收盘点位；
        N1:较低执行价格的期权多头头寸数量；
        N2:较高执行价格的期权多头头寸数量；
        N_underlying：1张标的资产期权基础资产是多少份单位净值.'''    
        Pt=P0*Pt_index/P0_index  #期权到期日标的资产基金净值数组
        put_long=N1*N_underlying*(np.maximum(K1-Pt,0)-P1) #期权到期日较低执行价格期权多头头寸的盈亏
        put_short=N2*N_underlying*(P2-np.maximum(K2-Pt,0)) #期权到期日较高执行价格期权空头头寸的盈亏
        bull_spread=put_long+put_short
        return Pt_index,put_long,put_short,bull_spread  #期权到期日牛市价差盈亏

    @staticmethod
    def equant_point_call(K1,C1,C2): 
        return 0 - C2 + (C1 + K1)

    @staticmethod
    def equant_point_put(K2,P1,P2): 
        return 0 + P1 - P2 + K2
     
    @staticmethod
    def margin_call(K1,K2,C1,C2,):
        '''
        付出权利金时没有保证金，
        得到权利金时付出行权价差的保证金'''
        if C1<C2:
            return K2 - K1
        else:
            return C1 - C2

    @staticmethod
    def margin_bear(K1,K2,C1,C2,):
        '''
        付出权利金时没有保证金，
        得到权利金时付出行权价差的保证金'''
        if C1>C2:
            return K2 - K1
        else:
            return C1 - C2
               
    def chose_contract(self, contracts, spred_type, current_price = None, std =  0.05,  round_type = 'down', type = 'bull'):
        """
        The function `chose_contract` takes in a list of contracts, a spread type, current price, standard
        deviation, and round type, and returns the contracts that meet the specified criteria.
        
        Args:
          contracts: A DataFrame containing information about different contracts.
          spred_type: The `spred_type` parameter is used to filter the contracts based on their type. It is
        a string that specifies the type of contract you want to choose.
          current_price: The current price of the underlying asset.
          std: The `std` parameter represents the standard deviation used to calculate the lower price
        bound. It is set to 0.02 by default.
          round_type: The parameter "round_type" determines how the "up" and "down" values are calculated.
        It can have two possible values: "down" or "up". If "round_type" is set to "down", the "up" value is
        rounded down to the nearest whole number and the. Defaults to down
        
        Returns:
          a tuple containing two dataframes: 'up' and 'down'.
        """

        # var
        # current_price = 4.99 ; 
        # std = 0.025; 
        # contracts = test; round_type  = 'down'
        
        contracts = self.process_conctracts(contracts)

        if current_price is None:
            current_price = float(contracts.标的收盘价.iloc[0])

        if type == 'bull':
            up = round(current_price * (1 - std), 2)
        elif type == 'bear':
            #如果是熊市看跌，低档位为亏损价格
            down = round(current_price * (1 + std), 2)

        contracts =  contracts.loc[(contracts.期权类型 == spred_type)]

        if round_type == 'down' :
            
            if type == 'bull':
                down = contracts.loc[(contracts.执行价.astype(float) <= up)].sort_values('执行价')['执行价'].iloc[-2]

                up = contracts.loc[(contracts.执行价.astype(float) <= up)].sort_values('执行价')['合约编码'].iloc[-1]            
                down = contracts.loc[(contracts.执行价.astype(float) <= down)].sort_values('执行价')['合约编码']
                if down.shape[0] == 1:
                    down = down.iloc[0]
                else:
                    down = down.iloc[-1]

            elif type == 'bear':
                up = contracts.loc[(contracts.执行价.astype(float) >= down)].sort_values('执行价')['合约编码'].iloc[1] 
                down = contracts.loc[(contracts.执行价.astype(float) >= down)].sort_values('执行价')['执行价'].iloc[0]
           
                down = contracts.loc[(contracts.执行价.astype(float) >= down)].sort_values('执行价')['合约编码']
                if down.shape[0] == 1:
                    down = down.iloc[0]
                else:
                    down = down.iloc[0]

        elif round_type == 'up':        
            up = contracts.loc[(contracts.执行价.astype(float) <= up)].sort_values('执行价')['合约编码'].iloc[-1]
            down = contracts.loc[(contracts.执行价.astype(float) >= down)].sort_values('执行价')['合约编码'].iloc[0]

        up = contracts.loc[contracts.合约编码 == up]
        down = contracts.loc[contracts.合约编码 == down]
        # upprice = up['收盘价']
        # downprice = down['收盘价']
        return (up,down)