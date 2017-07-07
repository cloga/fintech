# -*- coding: utf-8 -*-  
import tushare as ts
import pandas as pd 
import requests
from bs4 import BeautifulSoup
import re

def get_fund_histdata(fund_code):
    # 给定基金代码抓取历史数据
    form_data = {'page':1, 'perPage':100}
    fund_data = []
    # 基于好买的数据
    url0 = 'http://www.howbuy.com/fund/ajax/gmfund/history/huobi.htm?jjdm=' + str(fund_code) + '&flag=1'
    r = requests.post(url0, data=form_data)
    page_num = int(re.findall(re.compile(r'共(\d*)页'), r.text)[0])
    fund_data.append(pd.read_html(r.content, encoding='utf8', header=0)[0])
    for i in range(2, page_num+1):
        # print(i)
        form_data = {'page':i, 'perPage':100}
        r = requests.post(url0, data=form_data)
        fund_data.append(pd.read_html(r.content, encoding='utf8', header=0)[0])

    fund_data = pd.concat(fund_data)
    fund_data['fund_code'] = fund_code
    return fund_data

def get_fund_currdata(fund_code):
    # 给定基金代码抓取当前价格
    # 基于天天基金网数据
    fund_data = {}
    # fund_code = '519677'
    fund_data['fund_code'] = fund_code
    url0 = 'http://fund.eastmoney.com/' + str(fund_code) + '.html'
    r = requests.get(url0)
    # soup = BeautifulSoup(r.content,  "lxml")
    soup = BeautifulSoup(r.content,  "html5lib")

    fund_name = soup.find('div', 'fundDetail-tit').text
    dl = list(soup.find('dl', 'dataItem02').strings)
    previous_date = dl[2][:-1]
    fund_data['previous_date'] = previous_date
    previous_value = dl[3]
    fund_data['previous_value'] = previous_value
    previous_delta_rate_1d = dl[4]
    fund_data['previous_1d_delta_rate'] = previous_delta_rate_1d
    previous_delta_rate_3m = dl[6]
    fund_data['previous_delta_rate_3m'] = previous_delta_rate_3m
    previous_delta_rate_6m = dl[8]
    fund_data['previous_delta_rate_6m'] = previous_delta_rate_6m
    delta_rate = soup.find(id='gz_gszzl').text
    fund_data['delta_rate'] = delta_rate
    fund_data['fund_name'] = fund_name
    time = soup.find(id='gz_gztime').text
    fund_data['time'] = time
    price = soup.find(id='gz_gsz').text
    fund_data['price'] = price
    fund_data['delta'] = float(price) - float(previous_value)
    return fund_data

def get_hist_raw_data_equity(codes, start, end):
    data_list = []
    for k,v in codes.items():
        data_hist = ts.get_k_data(code= k, ktype='M', start=start, end=end)[['date', 'close']]
        data_hist.columns = ['date', k]
        data_list.append(data_hist)

    data_index = ts.get_k_data('000001', index=True, ktype='M', start=start, end=end)[['date', 'close']]
    data_index.columns = ['date', 'SH000001']
    data_list.append(data_index)
    data = reduce(lambda x,y: pd.merge(x, y, on='date', how='left'), data_list)
    data = data.fillna(method='ffill')
    data = data.set_index('date')

    # data[['601899', 'SH000001']].plot()
    # 改写列名增加股票名称
    # data_new = data.copy()
    # data_new.columns = list(map(lambda x: codes[x] + '-(' + x + ')', data_new.columns[:-1])) + ['上证指数-(SH000001)']
    # data_new.to_excel('data.xlsx') # 原始股价
    return data