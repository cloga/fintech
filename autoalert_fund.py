# -*- coding: utf-8 -*-  
import tushare as ts
import pandas as pd 
import requests
from bs4 import BeautifulSoup
import re
import datetime
from functools import reduce
from config import *
now_time = datetime.datetime.now()

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
    fund_data['time'] = pd.to_datetime(time[1:-1], yearfirst=True)
    price = soup.find(id='gz_gsz').text
    fund_data['price'] = price
    fund_data['delta'] = float(price) - float(previous_value)
    return fund_data



fund_currlist = []
for f in audit_list[fund_code_col]:
    fund_currlist.append(get_fund_currdata(f))

audit_data = pd.DataFrame(fund_currlist)

audit_data['date'] = audit_data['time'].map(lambda x: x.date())


# 按照当日估价与昨日均线判断金叉和死叉
def cal_dead_cross(row):
    if row['type_pre'] != '上升通道':
        return ''
    elif row['raw'] < row['moving 20']:
        return 'dead_cross_r_20'
    elif row['raw'] < row['moving 10']:
        return 'dead_cross_r_10'
    elif row['raw'] < row['moving 5']:
        return 'dead_cross_r_5'
    else:
        return ''


def cal_gold_cross(row):
    if row['raw'] != '下降通道':
        return ''
    elif row['raw'] > row['moving 20']:
        return 'gold_cross_r_20'
    elif row['raw'] > row['moving 10']:
        return 'glod_cross_r_10'
    elif row['raw'] > row['moving 5']:
        return 'glod_cross_r_5'
    else:
        return ''


date0 = max(audit_data['date'])

# 应该把这些历史数据存起来，没必要每天都去抓取一次
fund_hist_data = []
fund_mv_data = []
for f in audit_list[fund_code_col]:
    hist_data = get_fund_histdata(f)
    # hist_data = hist_data.set_index('净值时间')
    hist_data = hist_data.rename(columns={'累计净值': f})
    if len(fund_hist_data) == 0 :
        fund_hist_data = hist_data[['净值时间', f]]
    else:
        fund_hist_data = pd.merge(fund_hist_data, hist_data[['净值时间', f]], on='净值时间', how='outer')
    hist_data_raw = hist_data[['净值时间', f]]
    hist_data_raw['净值时间'] = pd.to_datetime(hist_data_raw['净值时间']).map(lambda x: x.date())
    hist_data_raw = hist_data_raw.set_index('净值时间')
    # 指定时间列
    hist_data_raw.columns.name = 'day'
    # 时间升序
    hist_data_raw = hist_data_raw.sort_index()
    # 只取最近20天
    hist_data_raw = hist_data_raw[f]

    if not date0 in list(hist_data_raw.index):
        # 把当天的实时数据放进去
        hist_data_raw[date0] = audit_data.loc[audit_data['fund_code']==f]['price'].values[0]
    hist_data_mv5 = hist_data_raw.rolling(window=5).mean().shift(1)
    hist_data_mv10 = hist_data_raw.rolling(window=10).mean().shift(1)
    hist_data_mv20 = hist_data_raw.rolling(window=20).mean().shift(1)
    moving_mean_data = pd.DataFrame({'raw': hist_data_raw[-21:], 'moving 5': hist_data_mv5[-21:], 'moving 10': hist_data_mv10[-21:], 'moving 20': hist_data_mv20[-21:]})
    moving_mean_data['code'] = f
    moving_mean_data['raw>mv5'] = moving_mean_data['raw'] > moving_mean_data['moving 5']
    moving_mean_data['mv5>mv10'] = moving_mean_data['moving 5'] > moving_mean_data['moving 10']
    moving_mean_data['mv10>mv20'] = moving_mean_data['moving 10'] > moving_mean_data['moving 20']
    moving_mean_data['type'] = '调整'
    moving_mean_data['type'].loc[moving_mean_data['raw>mv5'] & moving_mean_data['mv5>mv10'] & moving_mean_data['mv10>mv20']] = '上升通道'
    moving_mean_data['type'].loc[~moving_mean_data['raw>mv5'] & ~moving_mean_data['mv5>mv10'] & ~moving_mean_data['mv10>mv20']] = '下降通道'
    moving_mean_data['type_pre'] = moving_mean_data['type'].shift(1)
    moving_mean_data['dead_cross'] = moving_mean_data.apply(cal_dead_cross, axis=1)
    moving_mean_data['gold_cross'] = moving_mean_data.apply(cal_gold_cross, axis=1)
    moving_mean_data['name'] = audit_list[audit_list['fund_code']==f]['fund_name'].values[0]
    fund_mv_data.append(moving_mean_data)
    # fig = moving_mean_data.plot()
    # fig[0].get_figur().savefig( f +'.jpg')

fund_mv_data = pd.concat(fund_mv_data)

action = ''
current_action = fund_mv_data.loc[date0]
for i, row in current_action.iterrows():
    if len(row['dead_cross']) > 0:
        if row['dead_cross'] == 'dead_cross_r_5':
            action += '%s : %s 实时价格高于5日均线，可以考虑卖出 \n </p>' % (row['name'], row['code'])
        elif row['dead_cross'] == 'dead_cross_r_10':
            action += '%s : %s 实时价格高于10日均线，建议卖出 \n </p>' % (row['name'], row['code'])
        elif row['dead_cross'] == 'dead_cross_r_20':
            action += '%s : %s 实时价格高于20日均线，强烈建议卖出 \n </p>' % (row['name'], row['code'])
    elif len(row['gold_cross']) > 0:
        if row['gold_cross'] == 'gold_cross_r_5':
            action += '%s : %s 实时价格低于5日均线，可以考虑买入 \n </p>' % (row['name'], row['code'])
        elif row['gold_cross'] == 'gold_cross_r_10':
            action += '%s : %s 实时价格低于10日均线，建议买入 \n </p>' % (row['name'], row['code'])
        elif row['gold_cross'] == 'gold_cross_r_20':
            action += '%s : %s 实时价格低于20日均线，强烈建议买入 \n </p>' % (row['name'], row['code'])
    else:
        action += '%s : %s 建议观望 \n </p>' % (row['name'], row['code'])



equity = ts.get_today_all()
# equity = ts.get_realtime_quotes(equity_list)
equity = equity.loc[equity['code'].isin(list(equity_list))]
# print(equity)

# 发送邮件
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header

# 邮件对象:
msg = MIMEMultipart()
msg['From'] = from_addr
msg['Subject'] = Header(u'基金数据' + str(now_time), 'utf-8').encode()
msg['To'] = ';'.join(to_addr)
# 邮件正文是MIMEText:
msg_text = u'主人，今天的基金及股票数据如下：\n </p> -----基金实时数据-----：\n </p> %s \n </p>\
    -----今日操作建议-----：\n </p> %s \n </p> -----股票实时数据-----：\n </p> %s \n </p> -----基金的历史数据-----：\n </p> %s \n </p> ' \
     % (audit_data.to_html(bold_rows=True, index=False), action, equity.to_html(bold_rows=True, index=False), fund_mv_data.to_html(bold_rows=True))
msg.attach(MIMEText(msg_text, 'html', 'utf-8')) 


# part = MIMEApplication(open('final_data.xlsx','rb').read())
# part.add_header('Content-Disposition', 'attachment', filename=u"DA_data_alert.xlsx")
# msg.attach(part)

# msg = MIMEText('hello, send by Python...', 'plain', 'utf-8')
# 输入Email地址和口令:
# from_addr = raw_input('From: ')
import smtplib
server = smtplib.SMTP_SSL(smtp_server, 465)
# server = smtplib.SMTP(smtp_server, 25) # SMTP协议默认端口是25
server.set_debuglevel(1)
server.login(from_addr, password)
server.sendmail(from_addr, to_addr, msg.as_string())
server.quit()