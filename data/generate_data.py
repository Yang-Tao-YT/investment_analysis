#genenrate_data
import datetime
import os
import time
import json
import akshare as ak
import numpy as np
import pandas as pd
import requests

import config
from utils.basic import rename_dataframe

def trying (func):
    
    def new_fun(*args, **kwargs):
        count = 0
        while count < 10:
            print(count)
            try:
                return func(*args, **kwargs)
                break
            except Exception as e:
                print(e)
                count+=1
        
    return new_fun

class WindMode:
    def __init__(self,) -> None:
        from WindPy import w
        self.w = w
        self.w.start()
        pass

    def download_k_data(self, windcode : str = '510500', startdate : str = '2022-11-08', enddate : str= '2022-11-09') -> pd.DataFrame:
        '''
        date format : '%Y-%m-%d'
        '''
        columns = 'tradecode,exerciseprice,option_name,change,amount,open,highest,lowest,close,settlement_price,position,delta,gamma,vega,theta,rho'
        info , df = self.w.wset("optiondailyquotationstastics",
                    f'startdate={startdate};enddate={enddate};exchange=sse;windcode={windcode}.SH;field=date,{columns}', usedf = True)
        code, info = self.w.wset("optioncontractbasicinformation","exchange=sse;windcode=510500.SH;status=all;field=wind_code,sec_name,exercise_date", usedf = True)

        df = df.set_index('option_name')
        info = info.set_index('sec_name')

        df = df.join(info)
        df.index.name = 'option_name'
        df = df.reset_index(drop=False, )
        print(info)
        return df

class AkShare:

    em_code = {}

    def stock_zh_a_hist(
        self,
        symbol: str = "000001",
        period: str = "daily",
        start_date: str = "19700101",
        end_date: str = "20500101",
        adjust: str = "",
    ) -> pd.DataFrame:
        """
        东方财富网-行情首页-沪深京 A 股-每日行情
        https://quote.eastmoney.com/concept/sh603777.html?from=classic
        :param symbol: 股票代码
        :type symbol: str
        :param period: choice of {'daily', 'weekly', 'monthly'}
        :type period: str
        :param start_date: 开始日期
        :type start_date: str
        :param end_date: 结束日期
        :type end_date: str
        :param adjust: choice of {"qfq": "前复权", "hfq": "后复权", "": "不复权"}
        :type adjust: str
        :return: 每日行情
        :rtype: pandas.DataFrame
        """
        
        code = {'sz' : 0, 'sh' : 1}
        secid =  f"{code[symbol[:2]]}.{symbol[2:]}"

        adjust_dict = {"qfq": "1", "hfq": "2", "": "0"}
        period_dict = {"daily": "101", "weekly": "102", "monthly": "103"}
        url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
        params = {
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "klt": period_dict[period],
            "fqt": adjust_dict[adjust],
            "secid": secid,
            "beg": start_date,
            "end": end_date,
            "_": "1623766962675",
        }
        r = requests.get(url, params=params)
        data_json = r.json()
        if not (data_json["data"] and data_json["data"]["klines"]):
            return pd.DataFrame()
        temp_df = pd.DataFrame(
            [item.split(",") for item in data_json["data"]["klines"]]
        )
        temp_df.columns = [
            "日期",
            "开盘",
            "收盘",
            "最高",
            "最低",
            "成交量",
            "成交额",
            "振幅",
            "涨跌幅",
            "涨跌额",
            "换手率",
        ]
        temp_df.index = pd.to_datetime(temp_df["日期"])
        temp_df.reset_index(inplace=True, drop=True)

        temp_df["开盘"] = pd.to_numeric(temp_df["开盘"])
        temp_df["收盘"] = pd.to_numeric(temp_df["收盘"])
        temp_df["最高"] = pd.to_numeric(temp_df["最高"])
        temp_df["最低"] = pd.to_numeric(temp_df["最低"])
        temp_df["成交量"] = pd.to_numeric(temp_df["成交量"])
        temp_df["成交额"] = pd.to_numeric(temp_df["成交额"])
        temp_df["振幅"] = pd.to_numeric(temp_df["振幅"])
        temp_df["涨跌幅"] = pd.to_numeric(temp_df["涨跌幅"])
        temp_df["涨跌额"] = pd.to_numeric(temp_df["涨跌额"])
        temp_df["换手率"] = pd.to_numeric(temp_df["换手率"])

        return temp_df

    def __init__(self) -> None:
        print('initial akshare')
        
        self.ak = ak

    def current_em(self):
        option_daily_hist_em_df = self.ak.option_current_em()
        
        return option_daily_hist_em_df.loc[(option_daily_hist_em_df.名称.str.contains('ETF') )| 
                                           (option_daily_hist_em_df.名称.str.contains('科创'))
                                           ].sort_values('代码')

    def current_hs300sz_em(self)-> pd.DataFrame:
        """
        东方财富网-行情中心-期权市场
        http://quote.eastmoney.com/center
        :return: 期权价格
        :rtype: pandas.DataFrame
        """
        url = 'http://23.push2.eastmoney.com/api/qt/clist/get'
        params = {
            'cb': 'jQuery112407947059507078162_1685949825979',
            'pn': '1',
            'pz': '200000',
            'po': '1',
            'np': '1',
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': '2',
            'invt': '2',
            'fid': 'f3',
            'fs': 'm:12',
            'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f28,f11,f62,f128,f136,f115,f152,f133,f108,f163,f161,f162',
            '_': '1679304837515',
        }
        r = requests.get(url, params=params)
        data_text = r.text
        data_json = json.loads(data_text[data_text.find('{'):-2])
        temp_df = pd.DataFrame(data_json['data']['diff'])
        temp_df.columns = [
            '_',
            '最新价',
            '涨跌幅',
            '涨跌额',
            '成交量',
            '成交额',
            '_',
            '_',
            '_',
            '_',
            '_',
            '代码',
            '_',
            '名称',
            '_',
            '_',
            '今开',
            '_',
            '_',
            '_',
            '_',
            '_',
            '_',
            '_',
            '昨结',
            '_',
            '持仓量',
            '_',
            '_',
            '_',
            '_',
            '_',
            '_',
            '_',
            '行权价',
            '剩余日',
            '日增'
        ]
        temp_df = temp_df[[
            '代码',
            '名称',
            '最新价',
            '涨跌额',
            '涨跌幅',
            '成交量',
            '成交额',
            '持仓量',
            '行权价',
            '剩余日',
            '日增',
            '昨结',
            '今开'
        ]]
        temp_df['最新价'] = pd.to_numeric(temp_df['最新价'], errors='coerce')
        temp_df['涨跌额'] = pd.to_numeric(temp_df['涨跌额'], errors='coerce')
        temp_df['涨跌幅'] = pd.to_numeric(temp_df['涨跌幅'], errors='coerce')
        temp_df['成交量'] = pd.to_numeric(temp_df['成交量'], errors='coerce')
        temp_df['成交额'] = pd.to_numeric(temp_df['成交额'], errors='coerce')
        temp_df['持仓量'] = pd.to_numeric(temp_df['持仓量'], errors='coerce')
        temp_df['行权价'] = pd.to_numeric(temp_df['行权价'], errors='coerce')
        temp_df['剩余日'] = pd.to_numeric(temp_df['剩余日'], errors='coerce')
        temp_df['日增'] = pd.to_numeric(temp_df['日增'], errors='coerce')
        temp_df['昨结'] = pd.to_numeric(temp_df['昨结'], errors='coerce')
        temp_df['今开'] = pd.to_numeric(temp_df['今开'], errors='coerce')
        return temp_df

    def current_hs300risk_sz_em(self):
        """
        东方财富网-数据中心-特色数据-期权风险分析
        https://data.eastmoney.com/other/riskanal.html
        :return: 期权风险分析
        :rtype: pandas.DataFrame
        """
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            # 'cb' : 'jQuery112303430085114075474_1679382981124'
            'fid': 'f3',
            'po': '1',
            'pz': '5000',
            'pn': '1',
            'np': '1',
            'fltt': '2',
            'invt': '2',
            'ut': 'b2884a393a59ad64002292a3e90d46a5',
            'fields': 'f1,f2,f3,f12,f13,f14,f302,f303,f325,f326,f327,f329,f328,f301,f152,f154',
            'fs': 'm:12'
        }
        r = requests.get(url, params=params)
        data_json = r.json()
        temp_df = pd.DataFrame(data_json["data"]["diff"])
        temp_df.columns = [
            '-',
            '最新价',
            '涨跌幅',
            '期权代码',
            '-',
            '期权名称',
            '-',
            '-',
            '到期日',
            '杠杆比率',
            '实际杠杆比率',
            'Delta',
            'Gamma',
            'Vega',
            'Theta',
            'Rho',
        ]
        temp_df = temp_df[[
            '期权代码',
            '期权名称',
            '最新价',
            '涨跌幅',
            '杠杆比率',
            '实际杠杆比率',
            'Delta',
            'Gamma',
            'Vega',
            'Rho',
            'Theta',
            '到期日',
        ]]
        temp_df['最新价'] = pd.to_numeric(temp_df['最新价'], errors="coerce")
        temp_df['涨跌幅'] = pd.to_numeric(temp_df['涨跌幅'], errors="coerce")
        temp_df['杠杆比率'] = pd.to_numeric(temp_df['杠杆比率'], errors="coerce")
        temp_df['实际杠杆比率'] = pd.to_numeric(temp_df['实际杠杆比率'], errors="coerce")
        temp_df['Delta'] = pd.to_numeric(temp_df['Delta'], errors="coerce")
        temp_df['Gamma'] = pd.to_numeric(temp_df['Gamma'], errors="coerce")
        temp_df['Vega'] = pd.to_numeric(temp_df['Vega'], errors="coerce")
        temp_df['Rho'] = pd.to_numeric(temp_df['Rho'], errors="coerce")
        temp_df['Theta'] = pd.to_numeric(temp_df['Theta'], errors="coerce")
        temp_df['到期日'] = pd.to_datetime(temp_df['到期日'].astype(str)).dt.date
        return temp_df

    def current_risk_em(self):
        # shen hs300 
        tempdf = self.current_hs300risk_sz_em()
        option_risk_analysis_em_df = self.ak.option_risk_analysis_em()
        option_risk_analysis_em_df = pd.concat([option_risk_analysis_em_df, tempdf])
        return option_risk_analysis_em_df.sort_values('期权代码')

    def current_risk_shangjiao(self, date = None):
        if date is None:
            date = (datetime.datetime.now() + datetime.timedelta(-1)).strftime('%Y%m%d')
        option_risk_analysis_em_df = self.ak.option_risk_indicator_sse(date)
        return option_risk_analysis_em_df.sort_values('SECURITY_ID')

    def download_us(self,
                    symbol=f'SPXL', 
                    period="daily", 
                    start_date="20220101", 
                    end_date="22220501",
                    adjust="qfq"):

        for i in range(100,110):
            try:
                stock_us_hist_df = self.ak.stock_us_hist(symbol=f'{i}.{symbol}', period=period, start_date=start_date, end_date=end_date,
                                                    adjust=adjust)
                print(i)
            except:
                pass
        return stock_us_hist_df

    def current_expire_date_shangjiao(self, etf = '500ETF', trade_date = None):
        if trade_date is None:
            trade_date = datetime.datetime.strftime(datetime.date.today(), '%Y%m')
        self.ak.option_sse_codes_sina
        return self.ak.option_sse_expire_day_sina(trade_date=trade_date,symbol=etf)
        
    def current_avaliable_option_zhongjing_sina(self, code = 'hs300'):
        '''
        code : {'hs300', 'zz1000'}
        '''
        etf_funs = {'hs300' : self.ak.option_cffex_hs300_list_sina, 'zz1000' : self.ak.option_cffex_zz1000_list_sina}

        return list( etf_funs[code]().values())[0]
    
    def current_option_bar_zhongjing_sina(self, code):
        '''
        code : io2104
        '''
        # print(code)
        if 'io' in code:
            return self.ak.option_cffex_hs300_spot_sina(code)
        else:
            return self.ak.option_cffex_zz1000_spot_sina(code)

    def current_option_bar_zhongjing_explatform(self, code):
            if 'io' in code:
                start = time.time()
                end_month = code.split('o')[1]
                df = self.ak.option_finance_board(symbol="沪深300股指期权", end_month=end_month)
                print(time.time() - start)
                assert df.shape[0] % 2 == 0

                df['exercise'] = pd.DataFrame(df['instrument'].str.split('-', expand=True)).iloc[:,-1]
                df = df.iloc[:df.shape[0]//2, :].join(df.iloc[df.shape[0]//2:, :-1].reset_index(drop=True), rsuffix='_short')
                print(time.time() - start)
                return df

    def download_stock_etf_hist_k(self, symbol='sh515790', gateway ='dc', save_path = config.path_hist_k_data, if_save = True):

        if gateway == 'dc':
            data = self.stock_zh_a_hist(symbol, adjust='qfq')
            # print(data)
            data["日期"] = pd.to_datetime(data["日期"]).dt.date

        else:
            data = self.ak.fund_etf_hist_sina(symbol=symbol,)

        if if_save:
            data.to_csv(f'{save_path}/{symbol}.csv')
        return data

    def current_k_data_all_dongcai(self):
        return self.ak.stock_zh_a_spot_em()

    def current_k_etf_dongcai(self):
        return self.ak.fund_etf_spot_em()
    
    def obtain_index_global(self):
        index_investing_global_df = ak.index_investing_global(area="美国", symbol="标普500指数", period="每日", start_date="20100101", end_date="20220808")
        print(index_investing_global_df)

    def obtain_index(self):
        stock_zh_index_daily_df = ak.stock_zh_index_daily(symbol="sh000300")
        print(stock_zh_index_daily_df)

    def stock_etf_hist_dataloader(self, symbol='sh515790', gateway ='dc', save_path = config.path_hist_k_data):
        '''
        读取历史k线数据'''
        max_try = 10

        while max_try > 0:
            try:
                data = self.download_stock_etf_hist_k(symbol, gateway, save_path, if_save=False)
                break
            except Exception as e:
                print(e)
                max_try -= 1
        
        if max_try == 0:
            Warning('download stock k data error, obtain from local history folder')
            data = pd.read_csv(f'{save_path}/{symbol}.csv', index_col=0)

        if save_path is not None:
            data.to_csv(f'{save_path}/{symbol}.csv')

        return data
    
class YFinance:

    def __init__(self) -> None:
        import yfinance as yf

        self.yf = yf

    def download_single_stock(self, tickers= "SPXL", start="2017-01-01", end= None):
        PROXY_SERVER = config.PROXY_SERVER
        stock_price = self.yf.download(tickers= tickers, start=start, end=end, proxy=PROXY_SERVER)
        return stock_price

class Request:

    def __init__(self) -> None:
        print('inital request')
        self.session_sate = {}

    def current_option_avaliable_sina(self):
        response = requests.get('https://stock.finance.sina.com.cn/futures/api/openapi.php/StockOptionService.getStockName'
        ,headers={'referer' : 'https://stock.finance.sina.com.cn/option/quotes.html'})
        data = response.text[response.text.find('"data":'):].strip()
        data = eval(data[data.find('"data":') + len('"data":') :data.find('}') + 1])
        return data

    def current_avaliable_option_code_sina(self,underlying='510500', expire_date ="202212", symbol = None):
        '''
        某个expire date的全部执行价的代码
        underlying:'510500' 底层资产 '''
        if len(str(expire_date)) > 4:
             expire_date = str(expire_date)[-4:]
        else:
            expire_date =  str(expire_date)

        code = underlying + expire_date
        url = f"http://hq.sinajs.cn/list=OP_UP_{code},OP_DOWN_{code},s_sh{code[:-4]}"
        response = requests.get(url,headers={'referer' : 'https://stock.finance.sina.com.cn/option/quotes.html'})
        
        up = response.text[response.text.find("hq_str_OP_UP") : response.text.find(";\nvar")].replace('"', ",").split(",")
        up = [i[7:] for i in up if i.startswith("CON_OP_")]
        down = response.text[response.text.find("hq_str_OP_DOWN") : response.text.rfind(";\nvar")].replace('"', ",").split(",")
        down = [i[7:] for i in down if i.startswith("CON_OP_")]
        self.session_sate[underlying] = (up , down)
        return 

    def current_option_bar_shangjiao(self, underlying = '510500', expire_date = '202212', option = 'call'):
        '''
        某个expire date的全部执行价的当日行情数据
        underlying:'510500' 底层资产 '''
        if underlying not in self.session_sate:
            self.current_avaliable_option_code_sina(underlying, expire_date)

        url = 'https://hq.sinajs.cn/list=' + ",".join(['CON_OP_' + i for i in self.session_sate[underlying][0]])
        response = requests.get(url
        ,headers={'referer' : 'https://stock.finance.sina.com.cn/option/quotes.html'})
        texts = response.text.strip().split('var')
        dfs = []
        for i in texts[1:-1]:
            dfs.append(self._xinlang_single_option_process(i).set_index('字段').T)
            pass
        
        return pd.concat(dfs)

    def _xinlang_single_option_process(self, data_text):
        data_list = data_text[
            data_text.find('"') + 1 : data_text.rfind('"')
        ].split(",")
        field_list = [
            "买量",
            "买价",
            "最新价",
            "卖价",
            "卖量",
            "持仓量",
            "涨幅",
            "行权价",
            "昨收价",
            "开盘价",
            "涨停价",
            "跌停价",
            "申卖价五",
            "申卖量五",
            "申卖价四",
            "申卖量四",
            "申卖价三",
            "申卖量三",
            "申卖价二",
            "申卖量二",
            "申卖价一",
            "申卖量一",
            "申买价一",
            "申买量一 ",
            "申买价二",
            "申买量二",
            "申买价三",
            "申买量三",
            "申买价四",
            "申买量四",
            "申买价五",
            "申买量五",
            "行情时间",
            "主力合约标识",
            "状态码",
            "标的证券类型",
            "标的股票",
            "期权合约简称",
            "振幅",
            "最高价",
            "最低价",
            "成交量",
            "成交额",
        ]
        data_df = pd.DataFrame(
            list(zip(field_list, data_list)), columns=["字段", "值"]
        )
        return data_df

    def current_option_risk_shangjiao(self, underlying = '510500', expire_date = '202212', option = 'call'):
        '''
        某个expire date的全部执行价的当日risk数据
        underlying:'510500' 底层资产 '''
        # 获取code
        if underlying not in self.session_sate:
            self.current_avaliable_option_code_sina(underlying, expire_date)
        
        if option == 'call':
            codes = self.session_sate[underlying][0]
        else:
            codes = self.session_sate[underlying][1]

        url = 'https://hq.sinajs.cn/list=' + ",".join(['CON_SO_' + i for i in codes])
        response = requests.get(url
        ,headers={'referer' : 'https://stock.finance.sina.com.cn/option/quotes.html'})
        texts = response.text.strip().split('var')
        dfs = []
        for data_list in texts[1:-1]:
            data_list = data_list[
                data_list.find('"') + 1 : data_list.rfind('"')
            ].split(",")
            field_list = [
                "期权合约简称",
                "成交量",
                "Delta",
                "Gamma",
                "Theta",
                "Vega",
                "隐含波动率",
                "最高价",
                "最低价",
                "交易代码",
                "行权价",
                "最新价",
                "理论价值",
            ]
            dfs.append( pd.DataFrame(
                list(zip(field_list, [data_list[0]] + data_list[4:])),
                columns=["字段", "值"],
            ).set_index('字段').T)
        
        return pd.concat(dfs)

    def current_bar_single_etf_sina(self, code = 'sh510500'):
        url = f'https://hq.sinajs.cn/?list=sh510500'

        response  = requests.get(url, headers={'referer' : 'https://finance.sina.com.cn/fund/quotes/'}, timeout=6)
        series = (response.text[response.text.find('"') + 1 : response.text.rfind('"')].strip(',').split(','))
        index = ['名称','开盘价','昨收价','收盘价','最高价','最低价','drop','drop','成交量','成交额',
                '买一量','买一价','买二量','买二价','买三量','买三价','买四量','买四价','买五量','买五价',
                '卖一量','卖一价','卖二量','卖二价','卖三量','卖三价','卖四量','卖四价','卖五量','卖五价',
                '日期','分时','秒']
        
        assert len(index) == len(series)
        data =  pd.DataFrame(zip(index,series), columns=['index', 'value'])
        data.loc[data['index'] == '日期', 'value'] = pd.to_datetime(data.loc[data['index'] == '日期', 'value']).dt.date
        return data.loc[data['index'] != 'drop']

class DataLoader(Request,AkShare):

    def __init__(self,):
        super().__init__()
        super(Request, self).__init__()

def download_etf():
    aks = AkShare()
    for i in ['sh510500', 'sh510300']:
        aks.download_stock_etf_hist_k(i)

def main():
    path_to_save = config.path_to_save
    today = datetime.datetime.strftime( datetime.datetime.today(), '%Y%m%d')
    if not os.path.exists(f'{path_to_save}/{today}/'):
        os.makedirs(f'{path_to_save}/{today}/') 
    # shangjiao sina
    # brows = Browser()
    # brows.download_all_options_multi_date()
    # brows.browser.close()
    # shangjiao dongfangcaifu
    df = AkShare().current_em()
    today = datetime.datetime.strftime( datetime.datetime.today(), '%Y%m%d')
    df.to_csv(f'{path_to_save}/{today}/dongfangcaifu_{today}.csv')
    df = AkShare().current_risk_em()
    today = datetime.datetime.strftime( datetime.datetime.today(), '%Y%m%d')
    df.to_csv(f'{path_to_save}/{today}/dongfangcaifu_risk_{today}.csv')
    # zhongjing sina
    test = DataLoader()
    today = datetime.datetime.strftime( datetime.datetime.today(), '%Y%m%d')
    for i in test.current_avaliable_option_zhongjing_sina('hs300'):
        test.current_option_bar_zhongjing_sina(i).to_csv(f'{config.path_to_save}/{today}/{i}.csv')
           
    for i in test.current_avaliable_option_zhongjing_sina('zz1000'):
        test.current_option_bar_zhongjing_sina(i).to_csv(f'{config.path_to_save}/{today}/{i}.csv')
    # risk sina
    test = Request()
    codes = {'300ETF' :  '510300', '50ETF' :  '510050', '500ETF' :  '510500'}
    result = test.current_option_avaliable_sina()
    for underlying in set(result['cateList']):
        for contract in set(result['contractMonth']):
            test.current_option_risk_shangjiao(underlying=codes[underlying], expire_date=contract.replace('-', '')).to_csv(f"{config.path_to_save}/{today}/{underlying}_{contract.replace('-', '')}_call_risk.csv")
            test.current_option_risk_shangjiao(underlying=codes[underlying], expire_date=contract.replace('-', ''), option='short').to_csv(f"{config.path_to_save}/{today}/{underlying}_{contract.replace('-', '')}_short_risk.csv")


if __name__ == "__main__":
    # download_etf()
    # main()
    AkShare().stock_zh_a_hist('sh512480')
    dbbug = 1
