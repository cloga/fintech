import pandas as pd
import tushare as ts
import logging
import datetime
logging.basicConfig(filename='/home/ec2-user/fintech/log.log', level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(message)s')
logging.info('-----get_stocks_price starts -----')
FIN_TECH_HDF5 = '/home/ec2-user/fintech/fin_tech.h5'
STOCKS_PRICE_HDF5 = '/home/ec2-user/fintech/stocks_price.h5'
STOCKS_PRICE_HDF5_MONTH = '/home/ec2-user/fintech/stocks_price_month.h5'
stock_basics = pd.read_hdf(FIN_TECH_HDF5,'stock_basics', mode='r')

# 算一下beta数据
stock_beta = []
for i, code in enumerate(stock_basics['code']):
    logging.info('---- {0} ----get_stocks_price {1} starts -----'.format(str(i), str(code)))
    k_data = ts.get_k_data(code)
    k_data_m = ts.get_k_data(code, ktype='M')
    # 补充一下beta_total值 beta, 相关系数
    if len(k_data) == 0:
        corr_coef = 0
        beta_overall = 0
        beta = 0
        continue
    else:
        k_data = k_data.set_index('date')
        k_data_m = k_data_m.set_index('date')
        k_data_m['pre_close'] = k_data_m['close'].shift(1)
        k_data_m['return%'] = (k_data_m['close'] - k_data_m['pre_close']) / k_data_m['pre_close'] * 100
        # 把两个数据按照月份对齐
        merged_data = pd.merge(k_data_m[['return%']], sh_index_data_m[['return%']], left_index=True, right_index=True)
        merged_data = merged_data.dropna()
        corr_coef = merged_data['return%_x'].corr(merged_data['return%_y'])
        beta_overall = merged_data['return%_x'].std() ** 2 / merged_data['return%_y'].std() ** 2
        beta = corr_coef * beta_overall ** 0.5
        stock_beta.append({'code': code, 'corr_coef': corr_coef, 'beta_overall': beta_overall, 'beta': beta})
    k_data.reset_index().to_hdf(STOCKS_PRICE_HDF5, code, format='table', data_columns=True)
    k_data_m.reset_index().to_hdf(STOCKS_PRICE_HDF5_MONTH, code, format='table', data_columns=True)
    logging.info('-----get_stocks_price {0} finished -----'.format(str(code)))
logging.info('-----get_stocks_price finished -----')
# 把beta相关信息存入hdf
stock_beta_df = pd.DataFrame(stock_beta)
stock_beta_df.to_hdf(FIN_TECH_HDF5,'stock_beta_df', format='table', data_columns=True)

# 读出beta数据 join在一起
stock_beta_df = pd.read_hdf(FIN_TECH_HDF5,'stock_beta_df', mode='r')
stock_basics_merge = pd.merge(stock_basics, stock_beta_df, on='code')
# hdf5 支持按字段查询，需要通过data_columns指定
stock_basics_merge.to_hdf(FIN_TECH_HDF5,'stock_basics_merge', format='table', data_columns=True)