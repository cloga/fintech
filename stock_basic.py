import pandas as pd
import numpy as np
import tushare as ts
from functools import reduce
import tushare as ts
import logging
import multiprocessing as mul
import datetime
from datetime import timedelta
from pandas.tseries.offsets import BDay
logging.basicConfig(filename='/home/ec2-user/fintech/log.log', level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# from config import FIN_TECH_HDF5
FIN_TECH_HDF5 = '/home/ec2-user/fintech/fin_tech.h5'
# from config import SQL_URL
SQL_URL = 'sqlite://///home/ec2-user/fintech/fintech.db'
# 两融余额

import tushare as ts

# opDate:信用交易日期
# stockCode:标的证券代码
# securityAbbr:标的证券简称
# rzye:本日融资余额(元)
# rzmre: 本日融资买入额(元)
# rzche:本日融资偿还额(元)
# rqyl: 本日融券余量
# rqmcl: 本日融券卖出量
# rqchl: 本日融券偿还量

# opDate:信用交易日期
# stockCode:标的证券代码
# securityAbbr:标的证券简称
# rzye:融资余额(元)
# rzmre: 融资买入额(元)
# rqyl: 融券余量
# rqye: 融券余量(元)
# rqmcl: 融券卖出量
# rzrqye:融资融券余额(元)
start = str((datetime.date.today() - 20 * BDay()).date())
end = str((datetime.date.today() - BDay()).date())


def get_margin(start, end):
    sh_margins = ts.sh_margins(start=start, end=end)
    sz_margins = ts.sz_margins(start=start, end=end)
    margins = pd.concat([sh_margins, sz_margins])
    margins['rzmre_z'] = (margins['rzmre'] - margins['rzmre'].mean()) / margins['rzmre'].std()
    margins['rqmcl_z'] = (margins['rqmcl'] - margins['rqmcl'].mean()) / margins['rqmcl'].std()
    return margins

def get_margin_details(start, end):
    logging.info('geting sh_margin data')
    sh_margin = ts.sh_margin_details(start=start, end=end)
    logging.info('sh_margin data getted')
    logging.info(end + ' length is ' + str(len(sh_margin[sh_margin['opDate']==end])))
    period_range = pd.period_range(start=start, end=end, freq='D')
    sz_margin_list = []
    for d in period_range:
        logging.info('geting ' + str(d) + ' data')
        sz_margin_detail = ts.sz_margin_details(str(d))
        sz_margin_detail['opDate'] = str(d)
        sz_margin_list.append(sz_margin_detail)
    sz_margin = pd.concat(sz_margin_list)
    return pd.concat([sh_margin, sz_margin])

# margins = get_margin(start, end)


# margin_details = get_margin_details(start=start, end=end)

# margin_warning_list = []
# for s in margin_details['securityAbbr'].unique():
#    logging.info('----- 判断 **' + s + '** 的两融余额情况 -----')
#    margin_detail = margin_details[margin_details['securityAbbr'] == s].sort_values('opDate')
#    margin_detail['rzmre_z'] = (margin_detail['rzmre'] - margin_detail['rzmre'].mean()) / margin_detail['rzmre'].std()
#    margin_detail['rqmcl_z'] = (margin_detail['rqmcl'] - margin_detail['rqmcl'].mean()) / margin_detail['rqmcl'].std()
#    margin_warning = margin_detail[((margin_detail['rzmre_z']>3) | (margin_detail['rqmcl_z']<-3)) & (margin_detail['opDate']==end)]
#    if len(margin_warning)>0:
#       logging.info(margin_warning)
#        margin_warning_list.append(margin_detail)

# logging.info('-----margin_warning_list finished -----')
# 监控分配预案
profit_pre = ts.profit_data(top=100, year=2017)
# newly_data = ts.get_today_all()
# newly_data['update_date'] = str(datetime.date.today())
# profit_pre = pd.merge(profit_pre_raw, newly_data, how='left', on='code')[['code', 'name_x', 'year', 'report_date', 'divi', 'shares', 'trade', 'update_date']]
# profit_pre.columns = ['code', 'name', 'year', 'report_date', 'divi', 'shares', 'trade', 'update_date']
# profit_pre['divi_rate%'] = profit_pre['divi'] * 10 / profit_pre['trade'] 
forecast_data = ts.forecast_data(2017,4)
forecast_data = forecast_data.sort_values('report_date', ascending=False)
forecast_data = forecast_data.head(100)
logging.info('-----forecast_data finished -----')

# 可转债数据
cbonds = ts.new_cbonds(default=0)
cbonds['date'] = datetime.datetime.now()
# 可转债的代码不是字符
cbonds['bcode'] = cbonds['bcode'].astype(str)
cbonds.to_hdf(FIN_TECH_HDF5,'cbonds', format='table', data_columns=True)
logging.info('-----cbonds finished -----')

# 基本面数据
stock_basics = ts.get_stock_basics()
# code是index
stock_basics = stock_basics.reset_index()
#hdf5 只支持datetime类型不支持date类型
stock_basics['date'] = datetime.datetime.now()
stock_basics['roe'] = stock_basics['esp'] / stock_basics['bvps']
stock_basics['area'].ix[stock_basics['area']=='内蒙'] = '内蒙古'
stock_basics.to_hdf(FIN_TECH_HDF5,'stock_basics', format='table', data_columns=True)
logging.info('-----stock_basics finished -----')

# 数据写入sqlite

from sqlalchemy import create_engine

engine = create_engine(SQL_URL)
# margin_warning_df = pd.concat(margin_warning_list)
# pd.merge(stock_basics, margin_warning_df, left_index=True, right_on='stockCode')[list(margin_warning_df.columns) + ['industry']].to_sql('margin_warning', engine, index=False, if_exists='replace')
# margin_details.to_sql('margin_details', engine, index=False, if_exists='replace')
# margins.to_sql('margins', engine, index=False, if_exists='replace')
profit_pre.to_sql('profit_pre', engine, index=False, if_exists='replace')
forecast_data.to_sql('forecast_data', engine, index=False, if_exists='replace')
# stock_basics.to_sql('stock_basics', engine, index=False, if_exists='replace')
# writer = pd.ExcelWriter('/home/cloga0216/blog/blog/static/files/margin_date.xlsx')
# pd.concat(margin_warning_list).to_excel(writer, 'margin_warning', index=False)
# margin_details.to_excel(writer, 'margin_details', index=False)
# margins.to_excel(writer, 'margin', index=False)
# profit_pre.to_excel(writer, 'profit_pre', index=False)
# forecast_data.to_excel(writer, 'forecast_data', index=False)
# writer.save()
logging.info('----- finished -----')
