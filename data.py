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
    fund_data['time'] = time
    price = soup.find(id='gz_gsz').text
    fund_data['price'] = price
    fund_data['delta'] = float(price) - float(previous_value)
    return fund_data



fund_currlist = []

for f in audit_list:
    fund_currlist.append(get_fund_currdata(f))

audit_data = pd.DataFrame(fund_currlist)

fund_hist_data = []
for f in audit_list:
    hist_data = get_fund_histdata(f)
    # hist_data = hist_data.set_index('净值时间')
    hist_data = hist_data.rename(columns={'累计净值': f})
    if len(fund_hist_data) == 0 :
        fund_hist_data = hist_data[['净值时间', f]]
    else:
        fund_hist_data = pd.merge(fund_hist_data, hist_data[['净值时间', f]], on='净值时间', how='outer')

fund_hist_data = fund_hist_data.set_index('净值时间')

equity = ts.get_today_all()
# equity = ts.get_realtime_quotes(equity_list)
equity = equity.ix[equity['code'].isin(list(equity_list))]
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
msg_text = u'主人，今天的基金及股票数据如下：\n' + '基金数据：\n' + audit_data.to_html(bold_rows=True, index=False) + '股票数据：\n' + equity.to_html(bold_rows=True, index=False).to_html(bold_rows=True)
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