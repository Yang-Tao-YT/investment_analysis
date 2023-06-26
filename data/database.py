import config
import os 
import pandas as pd
path = config.path

os.listdir(path + '/option_data_history')

def _get_hs300_history_options(year):
    files = [pd.read_csv((path + f'/option_data_history/沪深300/{year}/' + i), encoding='gbk', dtype=object) for i in os.listdir(
        path + f'/option_data_history/沪深300/{year}')]
    files = pd.concat(files).sort_values('日期')
    return files

def _get_hs300_history():
    data = pd.read_csv(f'{config.path_hist_k_data}/{"sh510300"}.csv')
    return data


def _get_hs300_history():
    data = pd.read_csv(f'{config.path_hist_k_data}/{"sh510300"}.csv')
    return data

def _get_hs300_history_unadjust():
    data = pd.read_csv(f'{config.path_hist_k_data}/{"sh510300"}_不复权.csv')
    return data
