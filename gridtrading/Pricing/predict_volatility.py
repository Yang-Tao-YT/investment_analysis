"""
Author：查伦
Date：2023年04月24日
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from arch import arch_model
import statsmodels.api as sm
import statsmodels.tsa.api as smt
import scipy.stats as scs
from .volatility_cone_surface import get_rolling_volatility, transfer_price_logreturn

trade_days_year = 242


def tsplot(ts: pd.Series,
           lags: int = None,
           figsize=(16, 10),
           style='bmh'):
    """
    ts: 时间序列数据
    lags: PACF和ACF绘图的最大滞后阶数
    """
    with plt.style.context(style):
        plt.figure(figsize=figsize)
        layout = (3, 2)
        ts_ax = plt.subplot2grid(layout, (0, 0), colspan=2)
        acf_ax = plt.subplot2grid(layout, (1, 0))
        pacf_ax = plt.subplot2grid(layout, (1, 1))
        qq_ax = plt.subplot2grid(layout, (2, 0))
        pp_ax = plt.subplot2grid(layout, (2, 1))

        ts.plot(ax=ts_ax)
        ts_ax.set_title('Time Series Analysis Plots')
        smt.graphics.plot_acf(ts, lags=lags, ax=acf_ax, alpha=0.05)
        smt.graphics.plot_pacf(ts, lags=lags, ax=pacf_ax, alpha=0.05)
        sm.qqplot(ts, line='s', ax=qq_ax)
        qq_ax.set_title('QQ Plot')
        scs.probplot(ts, sparams=(ts.mean(), ts.std()), plot=pp_ax)
        plt.tight_layout()

    return


def get_best_model(ts: pd.Series):
    """
    ts: 时间序列数据
    """
    best_aic = np.inf
    best_order = None
    best_mdl = None
    pq_rng = range(5)
    for i in pq_rng:
        for j in pq_rng:
            tmp_mdl = smt.ARIMA(ts, order=(i, 0, j)).fit()
            tmp_aic = tmp_mdl.aic
            if tmp_aic < best_aic:
                best_aic = tmp_aic
                best_order = (i, j)
                best_mdl = tmp_mdl
    print('aic: {:6.5f} | order: {}'.format(best_aic, best_order))
    return best_aic, best_order, best_mdl


def vol_predict_garch(price_series: pd.DataFrame | pd.Series,
                      term: int = 30,
                      p: int = 1,
                      q: int = 1,
                      return_all: bool = False):
    """
    price_series: 标的资产价格序列
    term: 波动率预测期限
    p: garch标准残差滞后阶数
    q: garch条件方差滞后阶数
    return_all: 是否返回所有期限的波动率预测值
    """ 
    return_series = transfer_price_logreturn(price_series)
    model = arch_model(return_series * 100, vol="GARCH", dist="t", p=p, q=q)
    res = model.fit(disp="off")
    forecasts = res.forecast(horizon=term, reindex=False).variance.T
    annual_volatility = (forecasts ** 0.5 / 100) * (trade_days_year ** 0.5)
    prediction = annual_volatility.iloc[-1].squeeze()

    return prediction if not return_all else annual_volatility


def vol_backtest(price_history: pd.DataFrame | pd.Series,
                 term: int = 30,
                 lookback_window: int = 250,
                 step: int = 30,
                 p: int = 1,
                 q: int = 1):
    """
    price_history: 标的资产历史价格序列
    term: 预测未来N日波动率
    lookback_window: 回看窗口
    step: 滚动回测的步长
    """
    date_index = []
    result = {"Real": [], "Predicted": []}
    days = len(price_history)

    backtest_date_range = range(0, days - lookback_window - term, step)
    for dt in backtest_date_range:
        cross_section_ind = dt + lookback_window  # 截面日期
        date_index.append(price_history.index[cross_section_ind])

        # 预测波动率
        predicted_volatility = vol_predict_garch(price_history.iloc[dt:cross_section_ind],
                                                 term=term,
                                                 p=p, q=q)
        result["Predicted"].append(predicted_volatility)

        # 实际波动率
        prediction_term = cross_section_ind + term
        real_price = price_history.iloc[cross_section_ind:prediction_term, :]
        real_return = transfer_price_logreturn(real_price)
        real_volatility = real_return.std().squeeze() * trade_days_year ** 0.5  # 年化波动率
        result["Real"].append(real_volatility)

    garch_prediction = pd.DataFrame(result, index=date_index)

    return garch_prediction


if __name__ == "__main__":
    price_history = pd.read_excel("Pricing/data/510050.xlsx", index_col=0)
    vol_prediction = vol_backtest(price_history=price_history, term=30, step=5)

    vol_prediction.plot()
    plt.title("Volatility Prediction")
    plt.show(block=True)
