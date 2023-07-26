import pandas as pd
import os
from collections import defaultdict
import config
import json
import numpy as np
import matplotlib.pyplot as plt
from functools import partial
from data.generate_data import DataLoader
from utils.basic import rename_dataframe

def get_put(data):
    return data.loc[(data.tradecode.str.contains('P'))]

class Calculation:

    @staticmethod
    def vol(df : pd.DataFrame, window, ):
        df  = df.pct_change()
        return df.rolling(window).std() * np.sqrt(250)

class Bar:

    close = pd.Series(float)

    def update_bar(self, df):
        self.buy = df.buy
        self.sell = df.sell
        self.exercise = df.exercise
        self.close = df.close
        self.df = df
        # self.
        pass
    
    def find_price_by_exercise(self, exercise, option, direction):
        if option == 'call':
            if direction < 0:
                result = self.buy[self.exercise == exercise]
            else:
                result = self.sell[self.exercise == exercise]
        else:
            return self.buy_short[self.exercise_short == exercise]

        return result.squeeze()

class Strategy:

    def call_profit(self, exercise, current_price):
        return abs(max(current_price - exercise, 0))
    
    def put_profit(self, exercise, current_price):
        return abs(max(exercise -  current_price, 0))

    def butterfly(self, position:dict[list], current_price = None, percentage = None):
        '''
        current price:目前价格
        '''
        long = position['1']
        short = position['-1']

        cost = sum([i[-1] * i[-2] for i in long]) + sum([i[-1] * i[-2] for i in short])
        account = abs(sum([i[-1] * i[-2] for i in long])) + abs(sum([i[-1] * i[-2] for i in short]))
        
        def cal_profit(cost, current_price):
            balance = sum([self.call_profit(i[-3], current_price) * i[-1] for i in long]) + sum([self.call_profit(i[-3], current_price) * i[-1] for i in short]) 
            # profit = self.profit(k1, current_price) - 2 * self.profit(k2, current_price) + self.profit(k3, current_price) 
            profit = balance - cost
            return profit/ account
   
        exe_max = max([i[-3] for i in long] + [i[-3] for i in short])
        exe_min = min([i[-3] for i in long] + [i[-3] for i in short])

        cal_profit = partial(cal_profit, cost)
        if current_price is not None:
            if current_price == 'list':
                current_price = pd.DataFrame(np.arange(exe_min -  ((exe_max-exe_min))/20 ,exe_max + 2*((exe_max-exe_min))/20,((exe_max-exe_min))/20))
                
                profit = current_price.assign(profit=current_price[0].apply(cal_profit))
                profit = profit.set_index(0)
                profit = profit.round(2)
                if percentage is not None:
                    profit['percentage'] = profit.index / percentage
                    # profit.index = profit.index / percentage
                # profit = [cal_profit(i) for i in current_price]
            else:
                profit = cal_profit(current_price=current_price)
            return (profit,cost)

        else:

            return 

class Trading:

    def __init__(self,) -> None:
        self.position = {'1':[], '-1':[]}
        self.trading_history = []
        self.bar = Bar()
        pass

    def long( self, code, position,  price):
        self.on_order('long', code, price, position)
        pass

    def short(self, code, position,  price):
        self.on_order('short', code, price, position)

        pass

    def on_order(self, code, position, option, price = None, exercise = None):
        if price is None and exercise is not None:
            price = self.bar.find_price_by_exercise(exercise=exercise,option=option,direction=position)

        self.trading_history.append([code, exercise,price, position])
        self.position[str(int(position/abs(position)))].append([code, exercise, price, position])

        # with open('trade_logs.log', 'a') as file:

        #     file.write(str([code, exercise, price, position]) + '\n')
        pass

    def on_orders(self, code, trades):
        for i in trades:

            self.on_order(code, position=i[1],
                            option=i[0],
                            exercise=i[2])
        # with open('trade_logs.log', 'a+',) as file:

        #     file.write(f'new logs here_{datetime.datetime.today()}\n')                    


    def update_bar(self, df):
        self.bar.update_bar(df)

    def load_balance(self, code):
        if os.path.exists(f'{config.path_position}/{code}.log'):
            try:
                with open(f'{config.path_position}/{code}.log','r') as f:
                        self.position = json.load( f)
                
                print(self.position)
            except Exception as E:
                print(E)

    def cost(self, bar = None):
        if bar is None:
            bar = self.bar
        print(self.position)
        value = 0
        for direction in self.position:
            for position in self.position[direction]:
                value += position[-2] * position[-1]
        
        return value

    def balance(self, bar = None):
        if bar is None:
            bar = self.bar
        # print(self.position)
        value = 0
        for direction in self.position:
            for position in self.position[direction]:
                value += bar.close.loc[bar.exercise == position[1]].squeeze() * position[-1]
        
        return value

    def net_account(self, bar = None):
        if bar is None:
            bar = self.bar
        # print(self.position)
        value = 0
        for direction in self.position:
            for position in self.position[direction]:
                value += abs(position[-2] * position[-1])
        
        return value

    def profit(self, bar =None):
        
        cost = self.cost(bar)
        value = self.balance(bar)
        profit = value - cost
        returns = profit/self.net_account(bar)
        # print(f'returns of account is {returns * 100:.2f}% and net profit is {profit}')
        return  (returns, profit)

    def save_position(self, code):
        try:
            with open(f'{config.path_position}/{code}.log','w') as f:
                    json.dump(self.position, f)
            
            print(self.position)
        except Exception as E:
            print(E)

class Trading:
    position : pd.DataFrame
    def __init__(self,) -> None:
        
        self.trading_history = []
        self.bar = Bar()
        pass

    def update_bar(self, df):
        # self.bar.update_bar(df)
        self.bar.df = df

    def update_greek(self, df):
        # self.bar.update_bar(df)
        self.greek = df

    def load_position(self, position):
        self.position = position

    def cost(self):
        temp = (self.position.成本价 * self.position.实际持仓* self.position.持仓类型).sum() * 10000
        return temp

    def balance(self):
        temp = self.position.drop('最新价', axis = 1).join(self.bar.df).copy()
        temp = (temp.最新价 * temp.实际持仓 * temp.持仓类型).sum() * 10000
        return temp

    # def net_account(self, bar = None):
    #     if bar is None:
    #         bar = self.bar
    #     # print(self.position)
    #     value = 0
    #     for direction in self.position:
    #         for position in self.position[direction]:
    #             value += abs(position[-2] * position[-1])
        
    #     return value
    def update_position(self):
        index = self.position.index
        columns = self.position.columns
        temp_df = self.position.copy()
        temp_df = temp_df.drop('最新价', axis = 1, ).join(self.bar.df).copy()
        # 计算市值
        temp_df['合约市值'] =  temp_df[ '最新价'] * temp_df['实际持仓']*10000

        #计算盈亏
        temp_df[ '浮动盈亏'] =  ((temp_df['最新价']* temp_df[ '持仓类型']  -
                                             temp_df[ '成本价'] * temp_df[ '持仓类型'])
                                                        * temp_df['实际持仓']*10000)
        # temp_df.loc['统计', ['浮动盈亏', '合约市值']] =  temp_df[ ['浮动盈亏', '合约市值']].sum(axis = 0)
        #计算geek
        temp_df = temp_df.join(self.greek, lsuffix='old').copy()
        temp_df[ ['Delta', 'Gamma', 'Vega', 'Rho', 'Theta']] =     (temp_df[ ['Delta', 'Gamma', 'Vega', 'Rho', 'Theta']].mul(
                            temp_df['实际持仓'].squeeze() * self.position['持仓类型' ].squeeze()
                     * 10000 , axis = 0)  )
        
        # newgeek =  (self.position.loc[index, ['实际持仓'] ].squeeze() * self.position.loc[index, ['持仓类型'] ].squeeze()
        #              * 10000).mul( self.greek.loc[index, ['Delta', 'Gamma', 'Vega', 'Rho', 'Theta']]
        #                    , axis = 0)  
        # newgeek['Theta']  = (newgeek['Theta']  / 365)
        # self.position.loc[index, ['Delta', 'Gamma', 'Vega', 'Rho', 'Theta']] = newgeek.loc[index, ['Delta', 'Gamma', 'Vega', 'Rho', 'Theta']]

        #计算涨跌额
        
        temp_df[ '涨跌额'] = (temp_df[ '涨跌额']* temp_df[ '实际持仓'] * 
                                        10000 *  temp_df[ '持仓类型']).to_frame('涨跌额') 
        
        # self.position.insert(9,'涨跌额', list(percent.values) + [None])
        # self.position.loc[self.position.index, '涨跌额'] = percent.loc[self.position.index.drop('统计'), '涨跌额']
        # temp_df = temp_df.iloc[: , list(range(8)) + [len(temp_df.columns) - 1] + list(range(8, len(temp_df.columns)-1))]


        temp_df.loc['统计',['浮动盈亏', '合约市值', '涨跌额','Delta', 'Gamma', 'Vega', 'Rho', 'Theta'] ] = (
            temp_df.drop('统计')[ ['浮动盈亏', '合约市值', '涨跌额', 'Delta', 'Gamma', 'Vega', 'Rho', 'Theta'] ].sum(axis = 0))
        temp_df = temp_df.join(self.greek[ 'Delta'].to_frame('single delta'))
        # self.position.loc[index , '涨跌额'] = self.bar.df.loc[index , '涨跌额']* self.position.loc[index , '实际持仓'] * 10000 *  self.position.loc[index, '持仓类型']
        self.position = temp_df[['合约名称', '合约类型', '持仓类型', '实际持仓', '涨跌额', "涨跌幅", '成本价', '最新价', '合约市值', '行权价值',
       '浮动盈亏', '行权价' ,'Delta', 'Gamma', 'Vega', 'Theta', 'Rho']]
        
    def profit(self):
        
        cost = self.cost()
        value = self.balance()
        profit = value - cost
        # returns = profit/self.net_account(bar)
        # print(f'returns of account is {returns * 100:.2f}% and net profit is {profit}')
        return  round(profit, 2)

    def save_position(self, code):
        try:
            with open(f'{config.path_position}/{code}.log','w') as f:
                    json.dump(self.position, f)
            
            print(self.position)
        except Exception as E:
            print(E)

class StrangleOption(Strategy):


    pass

def load_current_data(date = '20221117', option = '500ETF11', source = 'sina'):
    if source == 'dfcf':
        data = pd.read_csv(f'{config.path_to_save}/{date}/dongfangcaifu_{date}.csv', index_col=0)
        if option is not None:
            data = data.loc[data.名称.str.contains(option)]

    else:
        datas = [i for i in os.listdir(f'{config.path_to_save}/{date}/')]
        if option is not None:
            datas = [i for i in datas if option in i]
        data = pd.read_csv(f'{config.path_to_save}/{date}/{datas[0]}', index_col=0)
    return data




if __name__ == '__main__':
    # data = load_current_data(date= '20221117', option = '500ETF_2022-11-23', source='sina')

    code = '500etf_2212'
    trad = Trading()
    loader = DataLoader()
    # loader.inital_akshare()

    # data = loader.current_option_bar_zhongjing_sina('io2212')
    data = loader.current_option_bar_shangjiao('510500', expire_date='202212')

    data = rename_dataframe(data)
    data = data.apply(pd.to_numeric,args=['ignore'])

    trad.update_bar(data)
    # # trad.load_balance(code)

    
    trades = [('call', -1, 6), ('call', 2, 6.25), ('call' , -1, 6.5)]
    trad.on_orders(code, trades)

    trad.balance()
    # trad.cost()
    trad.profit()
    trad.position
    stra = Strategy().butterfly(trad.position, 'list', percentage=3750)
    print(stra[0], stra[1])
    trad.save_position(code)
    

    # Strategy().butterfly(cost, excer, 6.25000)

    # print(trad.cost())
    # stra[0]['profit'].plot()
    # plt.show()
    1