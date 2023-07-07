from data.download_option_day import download
import config
import datetime
import os
from apscheduler.schedulers.blocking import BlockingScheduler
from utils.logs import make_print_to_file
from strategy.factor_cross_section import main as cross_section

def main():
    print('开始下载')
    data, greek = download()
    print(data.tail(5))
    path_to_save = config.path_to_save
    today = datetime.datetime.strftime( datetime.datetime.today(), '%Y%m%d')
    if not os.path.exists(f'{path_to_save}/{today}/'):
        os.makedirs(f'{path_to_save}/{today}/') 
        print(f'{path_to_save}/{today}/')

    data.to_csv(f'{path_to_save}/{today}/Kdata_{today}.csv')
    greek.to_csv(f'{path_to_save}/{today}/riskdata_{today}.csv')

def crontask():
    blocks = BlockingScheduler()
    blocks.add_job(main, 'cron', hour = 15, minute = 25,day_of_week = '0,1,2,3,4')
    blocks.start()

if __name__ == '__main__':
    make_print_to_file(path='/usr/local/app/app/app/cron/')
    main()
    cross_section()
    # crontask()