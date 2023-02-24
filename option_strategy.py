import pandas as pd
import os
from collections import defaultdict
import config
import json
import numpy as np
import matplotlib.pyplot as plt
from functools import partial
from data.genenrate_data import DataLoader
from basic import rename_dataframe

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


    # with open('trade_logs.log', 'a+',) as file:

    #     file.write(f'new logs here_{datetime.datetime.today()}\n')
        
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