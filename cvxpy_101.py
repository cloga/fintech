import pandas as pd
import cvxpy as cvx
import numpy as np
import tushare as ts
from functools import reduce 
from sqlalchemy import create_engine
# data = pd.read_excel('invest.xlsx', index_col=0)
# return_vec = data.values.T # 每个资产的时间序列表现

start = '2012-06-01'
end = '2017-06-30'
 
# codes = {'600660': '福耀玻璃', '002300': '太阳电缆', '000776': '广发证券', '000425': '徐工机械'
    # , '600009': '上海机场', '601618': '中国中冶', '600519': '贵州茅台', '002330': '得利斯', '601899': '紫金矿业', '601888': '中国国旅'}

codes = {'600000': '浦发银行', '600690': '青岛海尔', '601398': '工商银行', '000538': '云南白药'
    , '000651': '格力电器', '002352': '顺丰控股', '600016': '民生银行', '600369': '西南证券', '601111': '中国国旅', '000002', '万科A', '': '科大讯飞'}

    # , '000166': '申万宏源'


# stocks =  ts.get_stock_basics()
# engine = create_engine('sqlite:///fintech.db')
# stocks.to_sql('stocks_info', engine)
# stocks.to_excel('stocks.xlsx')

# codes = stocks['name'].to_dict()

data = ts.get_k_data('000001', index=True, ktype='M', start=start, end=end)[['date', 'close']]

data.columns = ['date', 'SH000001']

for k,v in codes.items():
    print(list(codes.keys()).index(k) + 1, k, v)
    data_hist = ts.get_k_data(code= k, ktype='M', start=start, end=end)
    if len(data_hist.columns)==0 :
        continue
    data_hist = data_hist[['date', 'close']]
    data_hist.columns = ['date', k]
    data = pd.merge(data, data_hist, on='date', how='left')

# data_list.append(data_index)

data = data.fillna(method='ffill')

data = data.set_index('date')

data = data[data.columns[data.count() == 61]]


# data[['601899', 'SH000001']].plot()
# 改写列名增加股票名称
data_new = data.copy()
data_new.columns = ['上证指数-(SH000001)'] + list(map(lambda x: codes[x] + '-(' + x + ')', data_new.columns[1:]))

data_new.to_excel('data.xlsx') # 原始股价

data_delta_raw = (data - data.shift(1)) / data.shift(1)

data_delta_raw = data_delta_raw['2012-07-01':]

data_delta_raw = data_delta_raw * 100 # 化为整数

# data_delta_raw[['601899', 'SH000001']].plot()

# for i in data_delta_raw.columns[:-1]:
#     beta = data_delta_raw['SH000001'].cov(data_delta_raw[i]) / (data_delta_raw['SH000001'].std() ** 2)
#     print(codes[i] + 'beta is:' + str(beta))

# 排除上证指数
data_delta = data_delta_raw[[c for c in data_delta_raw.columns if c != 'SH000001']]

data_delta_raw_new = data_delta_raw.copy()
# 上证指数在第一列
data_delta_raw_new.columns = ['上证指数-(SH000001)'] + list(map(lambda x: codes[x] + '-(' + x + ')', data_delta_raw_new.columns[1:])) + 

data_delta_raw_new.to_excel('data_delta_raw.xlsx') # 月度回报数据

return_risk = pd.DataFrame({'mean': data_delta_raw_new.mean(), 'std': data_delta_raw_new.std()})

# data_delta.to_excel('data_delta.xlsx')


# 计算相关矩阵

corr_matrix = data_delta_raw_new.corr()


# # Long only portfolio optimization.
# from cvxpy import *
# return_vec = data_delta.values.T
# Sigma = np.asmatrix(np.cov(return_vec))
# mu = np.asmatrix(data_delta.mean()).T
# n = len(data_delta.columns)
# w = Variable(n)
# gamma = Parameter(sign='positive')
# ret = mu.T*w 
# risk = quad_form(w, Sigma)
# 优雅的解法，给risk乘以一个系数，变动risk，沿着有效边界移动
# prob = Problem(Maximize(ret - gamma*risk), 
#                [sum_entries(w) == 1, 
#                 w >= 0])

# # Compute trade-off curve.
# SAMPLES = 100
# risk_data = np.zeros(SAMPLES)
# ret_data = np.zeros(SAMPLES)
# gamma_vals = np.logspace(-2, 3, num=SAMPLES)
# for i in range(SAMPLES):
#     gamma.value = gamma_vals[i]
#     prob.solve()
#     risk_data[i] = sqrt(risk).value
#     ret_data[i] = ret.value


# fig = plt.figure()
# ax = fig.add_subplot(111)
# plt.plot(risk_data, ret_data, 'g-')
# plt.xlabel('Standard deviation')
# plt.ylabel('Return')
# plt.show()

# risk_data[0]
# ret_data[0]

# data_delta = pd.read_excel('data.xlsx')


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
                    w >= 0,
                    ])
    prob0.solve()
    # print(w0.value)
    mu_min = ret.value

    risk_data = []
    ret_data = []
    weight_data = []
    # 沿着有效边界的顶点向右移动
    delta = cvx.Parameter(sign='positive')
    prob = cvx.Problem(cvx.Minimize(risk), 
           [cvx.sum_entries(w) == 1, 
            w >= 0,
            ret == mu_min + delta])

    for i in np.linspace(0, 5, sample):
        delta.value = i
        prob.solve()
        risk_min = cvx.sqrt(risk).value
        if risk_min == float('inf') or risk_min is None:
            break
        risk_data.append(cvx.sqrt(risk).value)
        # print(cvx.sqrt(risk).value)
        ret_data.append(ret.value)
        weight_data.append(w.value)
        # print(ret.value)
        # print(w.value)
    return risk_data, ret_data, weight_data

risk_data, ret_data, weight_data = efficeint_frontier_solver(data_delta, 500)

efficeint_frontier = pd.DataFrame({'std': risk_data, 'return': ret_data, 'notation': ''})

# risk_data[0]
# ret_data[0]

# 资本配置线
rf = 4.08 / 12 # 年化调整为月收益
level_cost = 2 # 借贷的费率倍率
shape_rate = float('-inf')
ret_p = float('-inf')
risk_p = float('-inf')
for i, risk in enumerate(risk_data):
    if shape_rate <= (ret_data[i] - rf) / risk:
        shape_rate = (ret_data[i] - rf) / risk
        ret_p = ret_data[i]
        risk_p = risk
        weight_data_0 = weight_data[i]

efficeint_frontier['notation'].loc[(efficeint_frontier['return'] == ret_p) & (efficeint_frontier['std'] == risk_p)] = '资本配置线切点'

# 不加杠杆时
sharp_ratio = (ret_p - rf) / risk_p

# 加杠杆之后的资本配置线向X轴旋转

sharp_ratio = (ret_p - rf * level_cost) / risk_p

capital_line = pd.DataFrame({'return' : [rf, ret_p, rf * level_cost + sharp_ratio * risk_p * 1.2], 'std': [0, risk_p, risk_p * 1.2], 'type': ['无风险资本', '最优资本配置线', '无风险借贷' + '-借贷成本' + str(rf * level_cost)]})

# reurn = rf + sharp_ratio * risk

# return = rf + sharp_ratio * risk * 1.2


# print('return', ret_p)
# print('risk', risk_p)

# 计算beta
data_beta = []
for i in data_delta_raw.columns[1:]:
    stock = {}
    stock['name'] = codes[i] + '-(' + i + ')'
    stock['r'] = data_delta_raw['SH000001'].corr(data_delta_raw[i])
    stock['beta_overall'] = data_delta_raw[i].std() ** 2 / data_delta_raw['SH000001'].std() ** 2
    stock['beta'] = stock['r'] * stock['beta_overall'] ** 0.5
    data_beta.append(stock)

data_beta = pd.DataFrame(data_beta)
data_beta['weight'] = list(map(lambda x: round(x, 4), weight_data_0.T.tolist()[0]))
# 有效前沿顶点对应的资产组合
data_beta['weight_min'] = list(map(lambda x: round(x, 4), weight_data[0].T.tolist()[0]))
data_beta = data_beta.set_index('name')

data_beta = pd.merge(return_risk, data_beta, left_index=True, right_index=True, how='left') # beta相关数据

# for i, weight in enumerate(weight_data_0.T.tolist()[0]):
    # print(list(codes.values())[i] + '权重为: ' + str(round(weight, 4)*100))



# fig = plt.figure()
# ax = fig.add_subplot(111)
# # plt.plot(stds, means, 'o', markersize=5)
# # plt.plot([risk_0], [ret_p], 'o')
# # plt.plot([risk_0, 0,  10], [ret_0, rf, sharp_ratio * 10 + rf ], 'r-')
# plt.plot(risk_data, ret_data, 'g-')
# plt.xlabel('Standard deviation')
# plt.ylabel('Return')
# plt.title('Efficient Frontier')
# plt.show()


# 效用最大化的点
# U = E(r) – 5A risk ^2 不带百分号
# Wp = [E(rp) – rf] /(A * risk_p ^2 ) 不带百分号
# A = 3
# wp = cvx.Variable(1)
# A = Parameter(sign='positive')
# lever_cost = 1
# if wp <= 1:
#     mu = wp * ret_p + (1-wp) * rf
# else:
#     wp * ret_p + (1-wp) * rf * (1 + lever_cost)
# risk_2 = wp ** 2 * risk_p ** 2
# U = mu - 0.005 * A * risk_2
# prob_p = cvx.Problem(cvx.Maximize(U), 
#                    [wp >= 0, 
#                     # wp <= 1,
#                     ])
# for i in range(1, 6):
#     A.value = i
#     prob_p.solve()
#     print('A', A.value)
#     print('mu', mu.value)
#     print('risk_2', risk_2.value)
#     print('wp', wp.value)
#     print('----')


rf_weights = []
for A in range(1, 6):
    rf_weight = {}
    rf_weight['A'] = A
    Wp = (ret_p - rf) / (A * risk_p ** 2) * 100
    rf_weight['无风险资产的权重'] = (1 - (round(Wp, 4)))*100
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

with pd.ExcelWriter('portifolio.xlsx') as writer:
    data_new.to_excel(writer, sheet_name='原始股价')
    data_delta_raw_new.to_excel(writer, sheet_name='月度回报数据')
    corr_matrix.to_excel(writer, sheet_name='相关矩阵')
    data_beta.to_excel(writer, sheet_name='最优风险资本组合')
    efficeint_frontier.to_excel(writer, sheet_name='efficeint_frontier', index=False)
    capital_line.to_excel(writer, sheet_name='资本配置线', index=False)
    rf_weights.to_excel(writer, sheet_name='加入无风险组合的权重')

