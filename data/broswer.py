
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import datetime
import pandas as pd
capa = DesiredCapabilities.CHROME
capa["pageLoadStrategy"] = "none"

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


class Browser:

    def __init__(self, path_to_save) -> None:
        #创建browser是浏览器对象
        capa = DesiredCapabilities.CHROME
        capa["pageLoadStrategy"] = "none"
        browser = webdriver.Chrome(desired_capabilities=capa)
        
        #访问某个url得到上述代码片段
        browser.get('https://stock.finance.sina.com.cn/option/quotes.html')
        browser.execute_script("window.stop();")
        self.browser = browser
        self.path_to_save = path_to_save
        time.sleep(3)

    def find_tables(self):
        self.table_up1 = self.browser.find_element(By.CLASS_NAME, 'table_up.fl')
        self.table_exe = self.browser.find_element(By.CLASS_NAME, 'table_xq.fl')
        self.table_down = self.browser.find_element(By.CLASS_NAME, 'table_down.fr')

    def tr_2_td(self, tr, **kargs):
        if 'text' in kargs:
            return [i.text for i in tr.find_elements(By.TAG_NAME, 'td')]
    
        return [i for i in tr.find_elements(By.TAG_NAME, 'td')]

    def tr_2_th(self, tr, **kargs):
        if 'text' in kargs:
            return [i.text for i in tr.find_elements(By.TAG_NAME, 'th')]
    
        return [i for i in tr.find_elements(By.TAG_NAME, 'th')]

    @trying
    def generate_table_up1(self,):

        datas = self.table_up1.find_elements(By.TAG_NAME, 'tr')
        text = [self.tr_2_td(datas[i], text = True)  if i != 0 else self.tr_2_th(datas[i], text = True) for i in range(len(datas)) ]
        df = pd.DataFrame(text)
        df.columns = df.loc[0]
        df  = df.drop([0])
        df = df.dropna()
        return df.reset_index(drop=True)


    def generate_table_down(self,):
        count = 0
        while count < 10:
            try:
                print(count)
                datas = self.table_down.find_elements(By.TAG_NAME, 'tr')
                text = [self.tr_2_td(datas[i], text = True)  if i != 0 else self.tr_2_th(datas[i], text = True) for i in range(len(datas)) ]
                break
            except:
                count += 1
        df = pd.DataFrame(text)
        df.columns = df.loc[0]
        df  = df.drop([0])
        df = df.dropna()
        return df.reset_index(drop=True)

    def generate_k_date(self):
        self.find_tables()
        df = self.generate_table_up1()
        trs = self.table_exe.find_elements(By.TAG_NAME, 'tr')
        trs = pd.Series([i.text for i in trs])
        trs.name = trs[0] ; trs = trs.drop([0,1]).reset_index(drop=True)
        down = self.generate_table_down()

        df = df.join(trs)
        df = df.join(down, rsuffix='_short')

        df.涨跌幅, main_call_index = df.涨跌幅.str.split('\n',expand=True)[0] , list(df.涨跌幅.str.split('\n',expand=True)[1] ).index('主')
        test = df.index.to_series()
        test.iloc[main_call_index] = '主'
        df.index = test
        return df

    def set_display_block(self):
        js1 = "document.getElementsByTagName('ul')[5].style.display='block'"
        self.browser.execute_script(js1)

        js1 = "document.getElementsByTagName('ul')[6].style.display='block'"
        self.browser.execute_script(js1)

    @trying
    def download_single_option_single_date(self, options, date, ):
        # count = 0
        # while 
        self.set_display_block()
        self.browser.find_element(By.CLASS_NAME, 'date.sel').find_element(By.LINK_TEXT, date).click()
        time.sleep(2)
        df = self.generate_k_date()
        today = datetime.datetime.strftime( datetime.datetime.today(), '%Y%m%d')
        date = self.browser.find_element(By.XPATH, '/html/body/div[3]/div[2]/div[1]/div[1]/div/span[1]').text
        df.to_csv(f'{self.path_to_save}/{today}/{options}_{date}.csv')

    def download_single_option_multi_date(self, options:str):
        self.set_display_block()
        date_set = [i.text for i in  self.browser.find_element(By.CLASS_NAME, 'date.sel').find_elements(By.TAG_NAME, 'li')]
        for date in date_set:
            self.download_single_option_single_date(options, date)

    def download_all_options_multi_date(self,):
        self.set_display_block()
        options = [i.text for i in self.browser.find_element(By.ID, 'option_cate').find_element(By.TAG_NAME, 'ul').find_elements(By.TAG_NAME, 'li')]
        
        for i in options:
            #跳转到options页面
            self.browser.find_element(By.ID, 'option_cate').find_element(By.TAG_NAME, 'ul').find_element(By.LINK_TEXT, i).click()
            time.sleep(5)
            self.download_single_option_multi_date(i)
