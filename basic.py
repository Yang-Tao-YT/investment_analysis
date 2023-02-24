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
        

        try:
            self.date = df.date
            self.open_interest = df.open_interest
        except:
            pass
        pass

    def __repr__(self) -> str:
        return f'open : {self.open}, close : {str(self.close)}, return : {str(self.close/self.open - 1)}'
        

name_2_symbol = {   
                'hs300':'sh510300', 
                '光伏':'sh515790',
                '新能源':'sh516160',
                '消费':'sz159928',
                '半导体' : 'sh512480',
                'zz500' : 'sh510500' ,
                'sz50' : 'sh510050',
                '创业板' : 'sz399102'}