"""
Author：查伦
Date：2023年04月28日
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import QuantLib as ql
from ..Pricing.quantlib_pricing import last_trade_date_month


def snowball_valuation(sample_path: pd.Series | np.ndarray,
                       ko: float = 1.03,
                       ko_lock: int = 0,
                       ki: float = 0.85,
                       principal: int = 1000000,
                       coupon_rate: float = 0.2,
                       risk_free_rate: float = 0.03) -> list[float, int | None, int | None]:
    """
    sample_path: 价格路径
    datetime_series: 日期序列
    month_end_index: 月末交易日的日期索引
    ko: 敲出比率
    ki: 敲入比率
    principal: 名义本金
    coupon_rate: 票息率
    risk_free_rate: 无风险利率
    """
    datetime_series = sample_path.index
    if isinstance(datetime_series[0], ql.Date):
        pass
    else:
        ql_transfer = np.vectorize(lambda dt: ql.Date(str(dt), "%Y-%m-%d"))  # 转换为ql.Date类型
        datetime_series = ql_transfer(datetime_series)
    
    # 行权，敲入，敲出价格
    strike_price = sample_path[0]
    ko_price, ki_price = strike_price * ko, strike_price * ki

    # 日期
    evaluation_date = datetime_series[0]
    maturity = (datetime_series[-1] - datetime_series[0]) / 365

    # 敲出日序列
    month_end_index = np.array([i for i, dt in enumerate(datetime_series) if last_trade_date_month(dt, evaluation_date.dayOfMonth()) and dt > evaluation_date + ql.Period(f"{ko_lock}m")])

    # 敲出日期（月末交易日）
    potential_ko_index = np.where(sample_path >= ko_price)[0]
    real_ko_index = np.intersect1d(potential_ko_index, month_end_index)

    result = [None, None, None]  # 价格，敲出日，敲入日

    if len(real_ko_index) != 0:
        # 发生敲出
        ko_date = datetime_series[real_ko_index[0]]
        ko_days = ko_date - evaluation_date
        result[1] = ko_days
        profit = ko_days / 365 * coupon_rate * principal * np.exp(-risk_free_rate * ko_days / 365)  # 按首个敲出日结算票息
    else:
        # 未敲出
        ki_index = np.where(sample_path <= ki_price)[0]  # 敲入日序列
        if len(ki_index) == 0:
            # 未敲出未敲入
            profit = principal * coupon_rate * maturity * np.exp(-risk_free_rate * maturity)  # 获得全部票息
        else:
            # 敲入后检查到期时标的价格
            result[2] = datetime_series[ki_index[0]] - evaluation_date
            last_price = sample_path[-1]
            profit = min(0, (last_price - strike_price) / strike_price * principal) * np.exp(
                -risk_free_rate * maturity)  # 标的价格若低于期初，则损失本金

    result[0] = profit

    return result


def snowball_backtest(price_series: pd.DataFrame | pd.Series,
                      window: int = 240,
                      step: int = 1,
                      **kwargs):
    """
    price_ts: 价格序列
    window: 窗口长度，等于雪球产品约定的存续天数，默认240个交易日（一年）
    step: 滚动回测步长，1为按日滚动回测
    """
    # 滚动回测
    res_dim0 = len(price_series) - window + 1
    result_values = list()
    for i in range(0, res_dim0, step):
        current_path = price_series[i:i + window].squeeze()
        result_values.append(snowball_valuation(sample_path=current_path, **kwargs))

    return pd.DataFrame(result_values,
                        index=price_series.index[np.arange(0, res_dim0, step)],
                        columns=["Profit", "KO Date", "KI Date"])


if __name__ == "__main__":
    zz500 = pd.read_excel("000905.xlsx", index_col=0)
    backtest_result = snowball_backtest(price_series=zz500,
                                        window=240,
                                        step=1)

