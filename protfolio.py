import pandas as pd
import cvxpy as cvx
import numpy as np
import tushare as ts
from functools import reduce 
# data = pd.read_excel('invest.xlsx', index_col=0)
# return_vec = data.values.T # 每个资产的时间序列表现

start = '2012-06-01'
end = '2017-06-30'
 
codes = {'600660': '福耀玻璃', '002300': '太阳电缆', '000776': '广发证券', '000425': '徐工机械'
    , '600009': '上海机场', '601618': '中国中冶', '600519': '贵州茅台', '002330': '得利斯', '601899': '紫金矿业', '601888': '中国国旅'}

# codes = {'600000': '浦发银行', '600690': '青岛海尔', '601398': '工商银行', '000538': '云南白药'
    # , '000651': '格力电器', '002352': '顺丰控股', '600016': '民生银行', '600369': '西南证券'}

    # , '000166': '申万宏源'


def efficeint_frontier_solver(data, sample=500):
    # data = data_delta
    # 算出有效边界的顶点
    n = len(data.columns)
    w = cvx.Variable(n)
    return_vec = data.values.T
    mu = np.asmatrix(data.mean()).T
    ret = mu.T * w
    C = np.asmatrix(np.cov(return_vec))
    risk = cvx.quad_form(w, C)
    prob0 = cvx.Problem(cvx.Minimize(risk), 
                   [cvx.sum_entries(w) == 1, 
                    w0 >= 0,
                    ])
    prob0.solve()
    # print(w0.value)
    mu_min = ret.value

    risk_data = []
    ret_data = []
    weight_data = []
    # 沿着有效边界的顶点向右移动
    delta = Parameter(sign='positive')
    prob = cvx.Problem(cvx.Minimize(risk), 
           [cvx.sum_entries(w) == 1, 
            w >= 0,
            ret == mu_min + delta])

    for i in np.linspace(0, 5, sample):
        delta.value = i
        prob.solve()
        risk_min = cvx.sqrt(risk).value
        if risk_min == inf or risk_min is None:
            break
        risk_data.append(cvx.sqrt(risk).value)
        # print(cvx.sqrt(risk).value)
        ret_data.append(ret.value)
        weight_data.append(w.value)
        # print(ret.value)
        # print(w.value)
        # efficeint_frontier = pd.DataFrame({'std': risk_data, 'return': ret_data})
    return risk_data, ret_data, weight_data

def cal_hist_return(data):
    '''
    计算回报率
    '''
    data_delta_raw = (data - data.shift(1)) / data.shift(1)
    data_delta_raw = data_delta_raw.iloc[1:, ]
    data_delta_raw = data_delta_raw * 100 # 化为整数
    # data_delta_raw[['601899', 'SH000001']].plot()
    # for i in data_delta_raw.columns[:-1]:
    #     beta = data_delta_raw['SH000001'].cov(data_delta_raw[i]) / (data_delta_raw['SH000001'].std() ** 2)
    #     print(codes[i] + 'beta is:' + str(beta))

    # 排除上证指数
    # data_delta = data_delta_raw.iloc[:, :-1]
    # data_delta_raw_new = data_delta_raw.copy()
    # data_delta_raw_new.columns = list(map(lambda x: codes[x] + '-(' + x + ')', data_delta_raw_new.columns[:-1])) + ['上证指数-(SH000001)']
    return data_delta_raw


def cal_capital_line(data_delta, rf):
    '''
    rf是年化收益率
    '''
    # data_delta_raw_new.to_excel('data_delta_raw.xlsx') # 月度回报数据
    return_risk = pd.DataFrame({'mean': data_delta_raw_new.mean(), 'std': data_delta_raw_new.std()})
    # data_delta.to_excel('data_delta.xlsx')

    # 计算相关矩阵
    data_delta_raw_new.corr()
    risk_data, ret_data, weight_data = efficeint_frontier_solver(data_delta, 500)

    # 资本配置线
    rf = rf / 12 # 年化调整为月收益
    shape_rate = -inf
    ret_p = -inf
    risk_p = -inf
    for i, risk in enumerate(risk_data):
        if shape_rate <= (ret_data[i] - rf) / risk:
            shape_rate = (ret_data[i] - rf) / risk
            ret_p = ret_data[i]
            risk_p = risk
            weight_data_0 = weight_data[i]

    # 计算beta
    data_beta = []
    for i in data_delta_raw.columns[:-1]:
        stock = {}
        stock['name'] = codes[i] + '-(' + i + ')'
        stock['r'] = data_delta_raw['SH000001'].corr(data_delta_raw[i])
        stock['beta_overall'] = data_delta_raw[i].std() ** 2 / data_delta_raw['SH000001'].std() ** 2
        stock['beta'] = stock['r'] * stock['beta_overall'] ** 0.5
        data_beta.append(stock)

    data_beta = pd.DataFrame(data_beta)
    data_beta['weight'] = list(map(lambda x: round(x, 4), weight_data_0.T.tolist()[0]))
    data_beta = data_beta.set_index('name')

    data_beta = pd.merge(return_risk, data_beta, left_index=True, right_index=True, how='left') # beta相关数据

    sharp_ratio = (ret_p - rf) / risk_p
    return data_beta, ret_p, risk_p

def cal_rf_weights(ret_p, risk_p, rf):
    # 效用最大化的点
    # U=E(r) – 5A risk ^2
    # Wp = [E(rp) – rf] /(A * risk_p ^2 )
    # A = 3
    # U= – 5A ^2
    rf_weights = []
    for A in range(1, 6):
        rf_weight = {}
        rf_weight['A'] = A
        Wp = (ret_p - rf) / (A * risk_p ** 2) * 100
        rf_weight['无风险资产的权重'] = 1 - (round(Wp, 4)*100)
        # print('A为', A, '的无风险资产权重为', 1 - (round(Wp, 4)*100))
        re = (1-Wp) * rf + Wp * ret_p
        # print('E(r)年化：', round(re * 12, 4))
        rf_weight['组合年化'] = round(re * 12, 4)
        risk = Wp * risk_p
        rf_weight['组合标准差'] = round(risk, 4)
        # print('Risk', round(risk, 4))
        # print('各风险资产的权重为:')
        for i, weight in enumerate(weight_data_0.T.tolist()[0]):
            rf_weight[list(codes.values())[i] + '-(' + list(codes.keys())[i] + ')'] = (round(weight, 4)*100)
            # print(list(codes.values())[i] , '权重为: ' , (round(weight, 4)*100))
        rf_weights.append(rf_weight)
        # print('------')

    rf_weights = pd.DataFrame(rf_weights)

    # with pd.ExcelWriter('portifolio.xlsx') as writer:
    #     data_new.to_excel(writer, sheet_name='原始股价')
    #     data_delta_raw_new.to_excel(writer, sheet_name='月度回报数据')
    #     data_beta.to_excel(writer, sheet_name='最优风险资本组合')
    #     efficeint_frontier.to_excel(writer, sheet_name='efficeint_frontier', index=False)
    #     rf_weights.to_excel(writer, sheet_name='加入无风险组合的权重')
    return rf_weights

