def rename_dataframe(df, ):
    columns = {'买价' : 'buy' , 
                '卖价' : 'sell', 
                '行权价' : 'exercise', 
                '最新价' : 'close',
                '买价_short' : 'buy_short' , 
                '卖价_short' : 'sell_short', 
                '行权价_short' : 'exercise_short',
                '看涨合约-买价'  : 'buy',
                '看涨合约-最新价'  : 'close',
                '看涨合约-卖价'    : 'sell', 
                '行权价' : 'exercise', 
                'bprice'  : 'buy',
                'lastprice'  : 'close',
                'sprice'    : 'sell', 
                '开盘价'    : 'open', 
                '昨收价' : 'pre_close', 
                '收盘价'  : 'close',
                '最高价'  : 'high',
                '最低价'    : 'low', 
                '成交量':'volume', 
                '成交额': 'amount',
                '日期' : 'date',
                '开盘'    : 'open', 
                '昨收' : 'pre_close', 
                '收盘'  : 'close',
                '最高'  : 'high',
                '最低'    : 'low', 
                }
    return df.rename(columns = columns)


class Bar:

    def update_bar(self, df ):
        self.open = float(df.open)
        self.high = float(df.high)
        self.low = float(df.low)
        self.close = float(df.close)
        self.volume = float(df.volume)
        

        for i in ['date','open_interest','pre_close']:
            try:
                setattr(self, i, float(df[i]))
            except:
                pass


        return self

    def __repr__(self) -> str:
        return f'open : {self.open}, close : {str(self.close)}, return : {str((self.close/self.pre_close - 1)* 100) } %'
        

name_2_symbol = {   
                'hs300':'sh510300', 
                '光伏':'sh515790',
                '新能源':'sh516160',
                '消费':'sz159928',
                '半导体' : 'sh512480',
                'zz500' : 'sh510500' ,
                'sz50' : 'sh510050',
                '创业板' : 'sz399102'}


def put_merge(合约前结算, 合约标的前收盘, 行权价):

    return min(合约前结算 + max(0.12 * 合约标的前收盘 - max(合约标的前收盘 - 行权价, 0), 0.07 * 行权价), 行权价) 

def call_merge(合约前结算, 合约标的前收盘, 行权价):

    return 合约前结算 + max(0.12 * 合约标的前收盘 - max(行权价 - 合约标的前收盘, 0), 0.07 * 行权价)
