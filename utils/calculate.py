# 认购期权义务仓开仓保证金＝[合约前结算价+Max（12%×合约标的前收盘价-认购期权虚值，7%×合约标的前收盘价）]×合约单位

# 认沽期权义务仓开仓保证金＝Min[合约前结算价+Max（12%×合约标的前收盘价-认沽期权虚值，7%×行权价格），行权价格] ×合约单位

# data.loc['10005180']
def calculate_put_margin(合约前结算价,
                     合约标的前收盘价,
                     认沽期权虚值,
                     行权价格,
                     合约单位):
    #Min[合约前结算价+Max（12%×合约标的前收盘价-认沽期权虚值，7%×行权价格），行权价格] ×合约单位
    return (min(合约前结算价 + max(0.12 * 合约标的前收盘价-认沽期权虚值, 0.07 * 行权价格), 行权价格)
             *合约单位)

def calculate_call_margin(合约前结算价,
                     合约标的前收盘价,
                     认购期权虚值,
                     合约单位):
    # [合约前结算价+Max（12%×合约标的前收盘价-认购期权虚值，7%×合约标的前收盘价）]×合约单位
    return (合约前结算价+max(0.12 * 合约标的前收盘价-认购期权虚值, 0.07 * 合约标的前收盘价)) * 合约单位

def calculate_mergin(_portfolio, _price):
        _price = _price.rename({'close' : '收盘'})
        _portfolio = _portfolio.rename(columns = {'close' : '收盘价' , '昨结' : '前收盘价'})
        for _conctract in _portfolio.index:
            if _portfolio.loc[_conctract, '期权类型'] == 'P':
                _portfolio.loc[_conctract, '保证金'] = calculate_put_margin(
                        float(_portfolio.loc[_conctract, '前收盘价']),
                        float(_price['前收盘']),
                        max(0, _price['收盘'] -  float(_portfolio.loc[_conctract, '执行价'])),
                        float(_portfolio.loc[_conctract, '执行价']),
                        1
                )
            
            elif _portfolio.loc[_conctract, '期权类型'] == 'C':
                _portfolio.loc[_conctract, '保证金'] = calculate_call_margin(
                        float(_portfolio.loc[_conctract, '前收盘价']),
                        float(_price['前收盘']),
                        max(0, float(_portfolio.loc[_conctract, '执行价']) -_price['收盘']),
                        1
                )
        return _portfolio