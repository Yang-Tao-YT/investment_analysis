from data.genenrate_data import main

from apscheduler.schedulers.blocking import BlockingScheduler


def crontask():
    blocks = BlockingScheduler()
    blocks.add_job(main, 'cron', hour = 15, minute = 25,day_of_week = '0,1,2,3,4')
    blocks.start()

if __name__ == '__main__':
    crontask()