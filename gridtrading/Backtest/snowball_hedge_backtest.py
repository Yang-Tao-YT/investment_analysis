"""
Author：查伦
Date：2023年04月28日
"""
from __future__ import annotations

import pandas as pd
import QuantLib as ql
from Hedge.snowball_dynamic_delta_hedge import SnowballHedger


def next_n_business_days(current_date: str, 
                         n: int):
    """
    获取当前日期之后第n个交易日
    """
    cur_date = ql.Date(current_date, "%Y-%m-%d")
    count = 0
    while count < n:
        cur_date = cur_date + ql.Period("1d")
        if ql.China().isBusinessDay(cur_date):
            count += 1

    return cur_date.to_date().strftime("%Y-%m-%d")



if __name__ == "__main__":
    zz500 = pd.read_excel("Backtest/000905.xlsx", index_col=0).squeeze() 
    shibor = pd.read_excel("SHIBOR_1年.xlsx", index_col=0).squeeze() / 100
    backtest_record = pd.DataFrame()

    snowball_kwargs = {
        "ki": 0.85,
        "ko": 1.05,
        "ko_lock": 0
    }
    backtest_start_date = "2018-01-03"
    backtest_cursor = backtest_start_date
    initial_position = 100000000
    position_cursor = initial_position

    while backtest_cursor < "2022-06-09":
        cur_date = ql.Date(backtest_cursor, "%Y-%m-%d")
        maturity_date = (cur_date + ql.Period("1y")).to_date().strftime("%Y-%m-%d")
        sb = SnowballHedger(price_series=zz500,
                            risk_free_rate_series=shibor,
                            sigma_window="1y",
                            start_date=backtest_cursor,
                            maturity_date=maturity_date,
                            initial_position=position_cursor,
                            **snowball_kwargs)
        current_backtest_df = sb.backtest_engine(method="fixed",
                                                 exp_upper_limit=0.03,
                                                 exp_down_limit=-0.03,
                                                 constant_sigma=True)
        
        backtest_record = pd.concat([backtest_record, current_backtest_df], axis=0)
        position_cursor = current_backtest_df.iloc[-1, 0]
        cur_end_date = current_backtest_df.index[-1].strftime("%Y-%m-%d")
        backtest_cursor = next_n_business_days(cur_end_date, 5)  # 5个交易日后重新建立新的雪球合约
        
    # sb.plot_backtest(backtest_record)
    # metrics_record = sb.metrics_backtest(backtest_record)
    backtest_record.to_csv("Backtest Record.csv")




