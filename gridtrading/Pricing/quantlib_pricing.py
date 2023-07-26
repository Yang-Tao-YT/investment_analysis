"""
Author：查伦
Date：2023年04月17日
"""

from __future__ import annotations

import QuantLib as ql
import numpy as np
import random
# import multiprocessing as mp
import multiprocessing_on_dill as mp
from scipy.stats import norm
import time


def get_bs_process(current_price: float = None,
                   risk_free_rate: float = None,
                   sigma: float = None,
                   calendar=ql.China(ql.China.SSE),
                   day_count=ql.Actual365Fixed()) -> ql.BlackScholesProcess:
    """
    获得BS随机过程对象
    -----------------------------
    current_price: 标的资产当前价格
    risk_free_rate: 无风险利率
    sigma: 标的资产波动率
    """
    # 输入参数
    s0 = ql.SimpleQuote(current_price)  # 当前价格
    r = ql.SimpleQuote(risk_free_rate)  # 无风险利率
    sigma = ql.SimpleQuote(sigma)  # 波动率

    # 利率和波动率期限结构
    riskFreeCurve = ql.FlatForward(0, calendar, ql.QuoteHandle(r), day_count)
    volatility = ql.BlackConstantVol(0, calendar, ql.QuoteHandle(sigma), day_count)

    # 标的资产价格的随机过程process对象
    process = ql.BlackScholesProcess(ql.QuoteHandle(s0),
                                     ql.YieldTermStructureHandle(riskFreeCurve),
                                     ql.BlackVolTermStructureHandle(volatility))

    return process


def get_heston_process(current_price: float = None,
                       risk_free_rate: float = None,
                       sigma: float = None,
                       v0: float = 0.005,
                       kappa: float = 0.8,
                       theta: float = 0.008,
                       rho: float = 0.2,
                       calendar=ql.China(ql.China.SSE),
                       day_count=ql.Actual365Fixed()):

    # 输入参数
    s0 = ql.SimpleQuote(current_price)  # 当前价格
    r = ql.SimpleQuote(risk_free_rate)  # 无风险利率

    # 利率和分红期限结构
    riskFreeCurve = ql.FlatForward(0, calendar, ql.QuoteHandle(r), day_count)
    dividendTS = ql.YieldTermStructureHandle(ql.FlatForward(0, 0, ql.Actual365Fixed()))

    initialValue = ql.QuoteHandle(ql.SimpleQuote(s0))
    process = ql.HestonProcess(riskFreeCurve, 
                               dividendTS, 
                               initialValue, 
                               v0, kappa, theta, sigma, rho)
    
    return process


def european_vanilla_option_pricing(evaluation_date: ql.Date = ql.Date().todaysDate(),
                                    option_type: str = "call",
                                    strike_price: float = None,
                                    exercise_date: ql.Date = None,
                                    current_price: float = None,
                                    risk_free_rate: float = None,
                                    sigma: float = None,
                                    method: str = "MCM",
                                    time_steps: int = 252,
                                    num_paths: int = 10000,
                                    seed: int = 2023) -> ql.Option:
    """
    对欧式香草期权定价
    ----------------------------
    evaluation_date: 当前估值日期
    option_type: 期权类型
        "call": 认购
        "put": 认沽
    strike_price: 行权价
    exercise_date: 执行日期
    current_price: 标的资产当前价格
    risk_free_rate: 无风险利率
    sigma: 标的资产波动率
    method: 估值方法
        "MCM": 蒙特卡洛模拟
        "Analytical": 欧式期权BSM解析解
    time_steps: 蒙卡下的模拟步数
    num_paths: 蒙卡下的模拟路径数量
    seed: 蒙卡下的随机种子
    """
    ql.Settings.instance().evaluationDate = evaluation_date

    if option_type == "call":
        option_obj = ql.Option.Call
    else:
        option_obj = ql.Option.Put

    # 期权对象
    option = ql.EuropeanOption(payoff=ql.PlainVanillaPayoff(option_obj, strike_price),
                               exercise=ql.EuropeanExercise(exercise_date))
    # 随机过程
    process = get_bs_process(current_price=current_price,
                             risk_free_rate=risk_free_rate,
                             sigma=sigma)

    # 定价引擎
    if method == "MCM":
        engine = ql.MCEuropeanEngine(process=process,
                                     traits="PseudoRandom",
                                     timeSteps=time_steps,
                                     requiredSamples=num_paths,
                                     seed=seed)
    else:
        engine = ql.AnalyticEuropeanEngine(process)

    option.setPricingEngine(engine)

    # 期权价格及Greeks
    # print(f"期权价格为：{option.NPV():.5f}")

    return option


def spread_option_pricing(evaluation_date: ql.Date = ql.Date().todaysDate(),
                          exercise_date: ql.Date = None,
                          option_type: str = "call",
                          spread_type: str = "bull",
                          current_price: float = None,
                          strike_price_1: float = None,
                          strike_price_2: float = None,
                          risk_free_rate: float = None,
                          sigma: float = None,):
    """
    BS对价差期权定价
    """
    ql.Settings.instance().evaluationDate = evaluation_date

    if option_type == "call":
        option_obj = ql.Option.Call
    else:
        option_obj = ql.Option.Put

    # 两个不同行权价格的期权对象
    if strike_price_1 > strike_price_2:
        option_high = ql.EuropeanOption(payoff=ql.PlainVanillaPayoff(option_obj, strike_price_1),
                                 exercise=ql.EuropeanExercise(exercise_date))
        option_low = ql.EuropeanOption(payoff=ql.PlainVanillaPayoff(option_obj, strike_price_2),
                                 exercise=ql.EuropeanExercise(exercise_date))
    else:
        option_high = ql.EuropeanOption(payoff=ql.PlainVanillaPayoff(option_obj, strike_price_2),
                                 exercise=ql.EuropeanExercise(exercise_date))
        option_low = ql.EuropeanOption(payoff=ql.PlainVanillaPayoff(option_obj, strike_price_1),
                                 exercise=ql.EuropeanExercise(exercise_date))       
    # 随机过程
    process = get_bs_process(current_price=current_price,
                             risk_free_rate=risk_free_rate,
                             sigma=sigma)

    # 定价引擎
    engine = ql.AnalyticEuropeanEngine(process)

    option_high.setPricingEngine(engine)
    option_low.setPricingEngine(engine)
    
    if spread_type == "bull":
        price = option_low.NPV() - option_high.NPV()
        delta = option_low.delta() - option_high.delta()
    else:
        price = option_high.NPV() - option_low.NPV()
        delta = option_high.delta() - option_low.delta()
    
    return price, delta


def bsformula_pricing(s0, r, T, k, sigma) -> float:
    """
    BS公式对欧式看涨期权定价
    ----------------------
    s0: 期初价格
    r: 无风险利率
    T: 到期时间
    k: 行权价格
    sigma: 波动率
    """
    nd1 = (np.log(s0 * np.exp(r * T) / k) +
           sigma ** 2 * T / 2) / (sigma * T ** 0.5)
    nd2 = (np.log(s0 * np.exp(r * T) / k) -
           sigma ** 2 * T / 2) / (sigma * T ** 0.5)
    return s0 * norm.cdf(nd1) - k * np.exp(-r * T) * norm.cdf(nd2)


def generate_simulated_path_generator(process: ql.BlackScholesProcess,
                                      evaluation_date: ql.Date,
                                      maturity_date: ql.Date,
                                      calendar=ql.China(ql.China.SSE),
                                      seed: int = 2023):
    """
    获得路径生成器对象
    --------------------
    process: 随机过程对象
    evaluation_date: 评估日期
    maturity_date: 终止日期
    seed: 随机种子
    """
    days = calendar.businessDaysBetween(
        evaluation_date, maturity_date, False, True)
    times = ql.TimeGrid((maturity_date - evaluation_date) / 365, days)
    # 高斯随机路径生成器
    rng = ql.UniformRandomSequenceGenerator(
        days, ql.UniformRandomGenerator(seed=seed))
    sequenceGenerator = ql.GaussianRandomSequenceGenerator(rng)
    pathGenerator = ql.GaussianMultiPathGenerator(
        process, list(times), sequenceGenerator, False)

    return pathGenerator


def last_trade_date_month(current_date: ql.Date | str,
                          n: int) -> bool:
    """
    判断当前日期是否是本月或下月N号之前（包含N号）的最后一个交易日，即雪球敲出日
    例: current_date = "2021-12-31", n = 31 -> True
        current_date = "2021-12-06", n = 8 -> False
        current_date = "2023-09-28", n = 1 -> True
    ------------------------------------------------------------
    date: 当前日期
    n: 每月n日，即雪球合约开始日的日期
    """
    if isinstance(current_date, str):
        current_date = ql.Date(current_date, "%Y-%m-%d")

    # 当日非交易日或当日为本月n号之后，直接返回False
    if not ql.China().isBusinessDay(current_date):
        return False

    # 寻找下一交易日
    next_business_date = current_date + 1
    while not ql.China().isBusinessDay(next_business_date):
        next_business_date += 1

    last_day_cur = ql.Date.endOfMonth(current_date)  # 当月最后一日
    last_day_next = ql.Date.endOfMonth(
        current_date + ql.Period("1m"))  # 下月最后一日
    cur_month_n = ql.Date(min(n, last_day_cur.dayOfMonth()),
                          last_day_cur.month(),
                          last_day_cur.year())  # 当月第n日，若n大于当月最后一日日期，取最后一日
    next_month_n = ql.Date(min(n, last_day_next.dayOfMonth()),  # 下月第n日
                           last_day_next.month(),
                           last_day_next.year())

    # 如果当前日期大于n日，那么只有可能成为下月N号之前的最后一个交易日
    if current_date.dayOfMonth() > n:
        return next_business_date > next_month_n
    else:
        return next_business_date > cur_month_n


def snowball_pricing_mcm(current_price: float | list[float],
                         strike_price: float,
                         risk_free_rate: float,
                         sigma: float,
                         principal: int,
                         coupon_rate: float,
                         ki: float,
                         ko: float,
                         ko_lock: int,
                         evaluation_date: str | ql.Date,
                         start_date: str | ql.Date,
                         maturity_date: str | ql.Date,
                         is_ki: bool = False,
                         num_paths: int = 300000,
                         only_price: bool = True,
                         seed: int = 2023):
    """
    使用蒙特卡洛方法对雪球衍生品进行定价（单进程）
    ------------------------------------------
    current_price: 标的资产当前价格
        float: 输入为标量（一个价格），返回该价格下的雪球定价结果
        list[float]: 输入为列表（多个价格），返回多个价格下的雪球定价结果（仅价格），一般用于差分法计算greeks
    strike_price: 行权价格（合约建立时标的资产价格）
    risk_free_rate: 无风险利率
    sigma: 标的资产波动率
    principal: 名义本金
    coupon_rate: 票息率
    ki: 敲入比率
    ko: 敲出比率
    ko_lock: 敲出锁定期月份
    evaluation_date: 定价评估日
    start_date: 合约开始日
    maturity_date: 合约到期日
    is_ki: 是否在评估日前敲入
    num_paths: 模拟路径数量
    only_price: 只输出价格
    seed: 随机种子
    """
    # 处理日期
    evaluation_date = ql.Date(evaluation_date, "%Y-%m-%d") if not isinstance(evaluation_date, ql.Date) else evaluation_date
    maturity_date = ql.Date(maturity_date, "%Y-%m-%d") if not isinstance(maturity_date, ql.Date) else maturity_date
    start_date = ql.Date(start_date, "%Y-%m-%d") if not isinstance(start_date, ql.Date) else start_date

    # 敲入敲出价格
    ko_price = strike_price * ko  # 敲出价格
    ki_price = strike_price * ki  # 敲入价格

    # 存续期
    maturity = (maturity_date - start_date) / 365

    # 判断评估日当日的敲入敲出状态, 当且仅当评估日在合约开始日之后
    if evaluation_date > start_date and isinstance(current_price, (int, float)):
        # 评估日是敲出观察日
        if current_price >= ko_price and last_trade_date_month(evaluation_date, start_date.dayOfMonth()):
            ko_days = evaluation_date - start_date
            profit = ko_days / 365 * coupon_rate * principal
            return profit
        elif current_price <= ki_price:
            is_ki = True

    # 当评估日到到期日期之间，已经没有交易日需要模拟，直接计算雪球损益
    if ql.China().businessDaysBetween(evaluation_date + 1, maturity_date) == 0 or evaluation_date == maturity_date:
        discount_days = maturity_date - evaluation_date
        if isinstance(current_price, (int, float)):
            # 曾经敲入
            if is_ki:
                profit = min(0, (current_price - strike_price) / strike_price * principal) * np.exp(
                    -risk_free_rate * discount_days / 365)
            # 未敲出未敲入
            else:
                profit = maturity * coupon_rate * principal * \
                    np.exp(-risk_free_rate * discount_days / 365)
            return profit
        else:
            # 列表形式下，循环计算每个价格对应的雪球状态
            res = np.zeros(len(current_price))
            for i in range(len(current_price)):
                cp = current_price[i]
                if cp <= ki_price or is_ki:
                    res[i] = min(0, (cp - strike_price) / strike_price * principal) * np.exp(
                        -risk_free_rate * discount_days / 365)
                elif cp >= ko_price and last_trade_date_month(evaluation_date, start_date.dayOfMonth()):
                    ko_days = evaluation_date - start_date
                    profit = ko_days / 365 * coupon_rate * principal
                    res[i] = profit
                else:
                    profit = maturity * coupon_rate * principal * \
                        np.exp(-risk_free_rate * discount_days / 365)
                    res[i] = profit
            return res

    # 交易日序列，每月最后一个交易日
    trade_date = ql.China().businessDayList(evaluation_date + 1, maturity_date)
    last_trade_date_index = np.array(
        [i for i, dt in enumerate(trade_date) if last_trade_date_month(dt, start_date.dayOfMonth())
         and dt > start_date + ql.Period(f"{ko_lock}m")]
    )

    # 获取BS过程对象
    first_price = current_price if isinstance(
        current_price, (int, float)) else current_price[0]
    process = get_bs_process(current_price=first_price,
                             risk_free_rate=risk_free_rate,
                             sigma=sigma)

    # 路径生成器
    paths_generator = generate_simulated_path_generator(process=process,
                                                        evaluation_date=evaluation_date,
                                                        maturity_date=maturity_date,
                                                        seed=seed)

    # 对每一条路径计算雪球的收益结构
    def snowball_valuation(sample_path: np.ndarray):
        """
        sample_path: 蒙特卡洛模拟中的一条路径
        """

        result = [None, None, None]  # 价格，敲出日，敲入日

        potential_ko_index = np.where(sample_path >= ko_price)[0]
        real_ko_index = np.intersect1d(
            potential_ko_index, last_trade_date_index)  # 敲出日序列
        if len(real_ko_index) != 0:
            # 发生敲出
            ko_date = trade_date[real_ko_index[0]]
            ko_days = ko_date - start_date
            discount_days = ko_date - evaluation_date
            result[1] = ko_days
            profit = ko_days / 365 * coupon_rate * principal * np.exp(
                -risk_free_rate * discount_days / 365)  # 按首个敲出日结算票息
        else:
            # 未敲出
            discount_days = maturity_date - evaluation_date
            ki_index = np.where(sample_path <= ki_price)[0]  # 敲入日序列
            if len(ki_index) == 0 and not is_ki:
                # 未敲出未敲入
                profit = principal * coupon_rate * maturity * \
                    np.exp(-risk_free_rate * discount_days / 365)  # 获得全部票息
            else:
                # 敲入后检查到期时标的价格
                result[2] = trade_date[ki_index[0]] - \
                    start_date if not is_ki else evaluation_date - start_date
                last_price = sample_path[-1]
                profit = min(0, (last_price - strike_price) / strike_price * principal) * np.exp(
                    -risk_free_rate * discount_days / 365)  # 标的价格若低于期初，则损失本金

        result[0] = profit

        return result

    # 价格，敲出次数，未敲入未敲出次数，敲入未敲出次数，亏损次数，平均敲出时间，平均存续时间，最大亏损
    res = 0 if only_price else np.zeros(8)
    # 开始模拟
    if isinstance(current_price, (int, float)):
        for _ in range(num_paths):
            samplePath = paths_generator.next().value()[0]
            temp_path = np.array([*samplePath])[1:]
            temp_res = snowball_valuation(temp_path)  # [价格，敲出日，敲入日]

            # 计算雪球各项指标
            if only_price:
                res += temp_res[0]
            else:
                res[0] += temp_res[0]
                if temp_res[1]:  # 敲出了
                    res[1] += 1
                    res[5] += temp_res[1]
                    res[6] += temp_res[1]
                else:
                    res[6] += (maturity * 365)
                    if temp_res[2]:  # 敲入了
                        res[3] += 1
                    else:  # 未敲入未敲出
                        res[2] += 1
                if temp_res[0] < 0:
                    res[4] += 1
                    res[7] = min(res[7], temp_res[0])

        if only_price:
            res /= num_paths
        else:
            res[:7] = res[:7] / num_paths

        return res
    else:
        res = np.zeros(len(current_price))
        if last_trade_date_month(evaluation_date, start_date.dayOfMonth()) and evaluation_date > start_date:
            # 找到在评估日已敲出的价格，直接计算票息收益填充至结果，这些价格不进入蒙卡循环的计算
            ko_price_index = np.where(np.array(current_price) >= ko_price)[0]
            if ko_price_index.shape[0] > 0:
                ko_days = evaluation_date - start_date
                profit = ko_days / 365 * coupon_rate * principal
                res[ko_price_index.min():] = profit
                current_price = current_price[:ko_price_index.min()]
        for _ in range(num_paths):
            samplePath = paths_generator.next().value()[0]
            first_path = np.array([*samplePath])[1:]
            for ind, price in enumerate(current_price):
                delta_ratio = price / current_price[0]  # 按照期初价S0计算平移比率
                temp_path = first_path * delta_ratio  # 将路径平移
                # 评估日已敲入
                if evaluation_date > start_date:
                    if price <= ki_price:
                        is_ki = True
                temp_res = snowball_valuation(temp_path)[0]
                res[ind] += temp_res
        res[:len(current_price)] /= num_paths

        return res


def snowball_pricing_mcm_mp(current_price: float | list[float],
                            strike_price: float,
                            risk_free_rate: float,
                            sigma: float,
                            principal: int,
                            coupon_rate: float,
                            ki: float,
                            ko: float,
                            evaluation_date: str,
                            start_date: str,
                            maturity_date: str,
                            is_ki: bool = False,
                            ko_lock: int = 0,
                            num_paths: int = 300000,
                            only_price: bool = True,
                            seed: int = 2023,
                            num_cores: int = 20,
                            verbose: bool = False):
    """
    使用蒙特卡洛方法对雪球衍生品进行定价（多进程）
    ----------------------------------------------
    current_price: 标的资产当前价格
        float: 输入为标量（一个价格），返回该价格下的雪球定价结果
        list[float]: 输入为列表（多个价格），返回多个价格下的雪球定价结果（仅价格），一般用于差分法计算greeks
    strike_price: 行权价格（合约建立时标的资产价格）
    risk_free_rate: 无风险利率
    sigma: 标的资产波动率
    principal: 名义本金
    coupon_rate: 票息率
    ki: 敲入比率
    ko: 敲出比率
    ko_lock: 敲出锁定期月份
    evaluation_date: 定价评估日
    start_date: 合约开始日
    maturity_date: 合约到期日
    is_ki: 是否在评估日前敲入
    num_paths: 模拟路径数量
    only_price: 只输出价格
    seed: 随机种子
    num_cores: 进程数量，最大不超过mp.cpu_counts()
    verbose: 是否print结果
    """
    random.seed(seed)

    num_cores = min(num_cores, mp.cpu_count())
    num_paths_per_process = num_paths // num_cores

    result_list = []
    pool = mp.Pool(num_cores)
    for current_seed in random.sample(range(1000), num_cores):
        temp = pool.apply_async(snowball_pricing_mcm,
                                args=(current_price, strike_price, risk_free_rate, sigma, principal,
                                      coupon_rate, ki, ko, ko_lock, evaluation_date, start_date,
                                      maturity_date, is_ki, num_paths_per_process, only_price,
                                      current_seed))
        result_list.append(temp)
    pool.close()
    pool.join()
    
    # 处理日期
    evaluation_date = ql.Date(evaluation_date, "%Y-%m-%d") if not isinstance(evaluation_date, ql.Date) else evaluation_date
    maturity_date = ql.Date(maturity_date, "%Y-%m-%d") if not isinstance(maturity_date, ql.Date) else maturity_date
    start_date = ql.Date(start_date, "%Y-%m-%d") if not isinstance(start_date, ql.Date) else start_date

    if isinstance(current_price, (int, float)):
        if only_price or (start_date < evaluation_date and last_trade_date_month(evaluation_date, start_date.dayOfMonth()) and current_price >= strike_price * ko) or ql.China().businessDaysBetween(evaluation_date + 1, maturity_date) == 0 or evaluation_date == maturity_date:
            res = np.mean([i.get() for i in result_list])
            if verbose:
                print(f"雪球价格:{res:.4f}")
        else:
            res = np.zeros(7)
            min_loss = 0
            for i in result_list:
                temp_res = i.get()
                res += temp_res[:7]
                min_loss = min(min_loss, temp_res[7])
            res /= num_cores
            res = np.append(res, min_loss)
            res = {
                "雪球价格": res[0],
                "敲出占比": res[1],
                "未敲出未敲入占比": res[2],
                "敲入未敲出占比": res[3],
                "亏损占比（敲入未敲出且到期时看跌期权为ITM）": res[4],
                "平均敲出月份": res[5] / 30,
                "平均存续月份": res[6] / 30,
                "最大亏损": res[7]
            }
            if verbose:
                for i, j in res.items():
                    print(f"{i}:{j:.4f}")

        return res
    else:
        res = np.zeros(len(current_price))
        for i in result_list:
            res += i.get()

        return res / num_cores


def calculate_coupon_snowball(**kwargs):
    """
    计算雪球价值为0时的理论票息
    基于蒙卡为雪球定价时，雪球价格与票息是线性关系，我们可用线性插值法直接获取价格为0时的理论票息
    -------------------------------------------------------------------------------------
    kwargs: 雪球参数
    """
    snowball_kwargs = kwargs.copy()
    snowball_kwargs["evaluation_date"] = snowball_kwargs["start_date"]
    # 任意选择两个初始票息，计算价格
    coupon_rate_one, coupon_rate_two = 0.1, 0.2
    snowball_kwargs["coupon_rate"] = coupon_rate_one
    price_one = snowball_pricing_mcm_mp(**snowball_kwargs)
    snowball_kwargs["coupon_rate"] = coupon_rate_two
    price_two = snowball_pricing_mcm_mp(**snowball_kwargs)
    # 计算斜率，截距，x轴截距（理论票息）
    slope = (price_two - price_one) / (coupon_rate_two - coupon_rate_one)
    intercept = price_one - slope * coupon_rate_one
    x_intercept = -intercept / slope

    return x_intercept


if __name__ == "__main__":
    start_time = time.time()  # 程序开始时间
    snowball_kwargs = {
        "current_price": 103,
        "strike_price": 100,
        "risk_free_rate": 0.03,
        "sigma": 0.15,
        "principal": 1000000,
        "coupon_rate": 0.05,
        "ki": 0.85,
        "ko": 1.05,
        "ko_lock": 2,
        "evaluation_date": "2022-10-10",
        "start_date": "2022-06-21",
        "maturity_date": "2023-06-20",
        "is_ki": True
    }
    # coupon_rate = calculate_coupon_snowball(**snowball_kwargs)
    price = snowball_pricing_mcm_mp(**snowball_kwargs,
                                    seed=2023,
                                    verbose=True,
                                    only_price=True)
    end_time = time.time()  # 程序结束时间
    print(f"\n程序运行时间：{end_time - start_time:.10f}秒")
