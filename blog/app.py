from flask import render_template
import datetime
from flask import request, url_for
from flask import Flask, render_template_string
import json
import pandas as pd
from flask_nav import Nav
from flask_nav.elements import Navbar, View
# from flask_flatpages import FlatPages, pygments_style_defs
# from flask_flatpages.utils import pygmented_markdown
import tushare as ts
from sqlalchemy import create_engine

# echarts
from pyecharts import Scatter3D
from pyecharts import Bar
import random
# from pyecharts.utils import json_dumps
from pyecharts import Kline
from pyecharts import Line, Grid
from flask import jsonify

# 导入配置文件
import config
# 使用bootstrap模板
from flask_bootstrap import Bootstrap
app = Flask(__name__)
app.url_map.strict_slashes = False
Bootstrap(app)

# 导入配置文件
app.config.from_object(config)

engine = create_engine(app.config['SQL_URL'])

# 添加导航栏
nav=Nav()
@nav.navigation()
def mynavbar():
    return Navbar(
        app.config['SITE_NAME']
        , View('Home', 'index')
#        , View('Table_demo', 'get_table_demo')
        , View('基本面', 'get_stock_basics')
        , View('获取实时股价', 'get_realtime_data_multi')
        , View('可转债', 'get_cbond_data')
        , View('业绩预告', 'get_forecast_data')
        , View('分红预案', 'get_profit_pre')
#         , View('两融异常', 'get_margin_warning')
       , View('个股历史相似走势', 'get_stock_similar_days')  
#        , View('直播网站榜单', 'get_live_data')  
    )

# ...

nav.init_app(app)

@app.route('/get_price_trends', methods=['GET'])
def get_price_trends():
    return render_template("basic.html")

# echarts 数据
def scatter3d():
    data = [generate_3d_random_point() for _ in range(80)]
    range_color = [
        '#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf',
        '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
    scatter3D = Scatter3D("3D scattering plot demo", width=1200, height=600)
    scatter3D.add("", data, is_visualmap=True, visual_range_color=range_color)
    return scatter3D


def generate_3d_random_point():
    return [random.randint(0, 100),
            random.randint(0, 100),
            random.randint(0, 100)]

from pyecharts import Map

from pyecharts import Page, Grid

@app.route('/')
def index():
    stock_basics = pd.read_hdf(app.config['FIN_TECH_HDF5'], 'stock_basics', mode='r')
    area_count = stock_basics.groupby('area')['code'].count().reset_index()
    area_sum = stock_basics.groupby('area')['totalAssets'].sum().reset_index()    
    value_count = list(area_count['code'])
    attr_count = list(area_count['area'])
    value_sum = list(area_sum['totalAssets'].astype(int))
    attr_sum = list(area_sum['area'])    
    map_count = Map("上市公司分布-公司数", width=1200, height=600)
    map_count.add("", attr_count, value_count, maptype='china', is_visualmap=True, visual_range=[0, 400], 
                  is_map_symbol_show=False, visual_text_color='#000')
    map_sum = Map("上市公司分布-公司市值", width=1200, height=600)
    map_sum.add("", attr_sum, value_sum, maptype='china', is_visualmap=True, visual_range=[10000000, 1000000000],
                  is_map_symbol_show=False, visual_text_color='#000')
    page = Page()
    page.add(map_count)
    page.add(map_sum)    
#     grid = Grid(width="100%")
#     grid.add(map_count, grid_left="60%")
#     grid.add(map_sum, grid_right="60%")
    return render_template('chart.html',
                           myechart=page.render_embed(),
                           host=app.config['REMOTE_HOST'],
#                            my_option=json_dumps(page.options),
                           script_list=page.get_js_dependencies())

    #    return render_template("basic.html")

stock_basics_columns = [{'field': 'code'
                      , 'title': '股票代码'
                      , "sortable": True}
                     , {'field': 'name'
                        , 'title': '股票名称'
                        , "sortable": True}
                     , {'field': 'beta_overall'
                        , 'title': '总beta'
                        , "sortable": True}
                     , {'field': 'beta'
                        , 'title': '有杠杆beta'
                        , "sortable": True}
                     , {'field': 'corr_coef'
                        , 'title': '和上证的相关系数'
                        , "sortable": True}                        
                     , {'field': 'industry'
                        , 'title': '所属行业'
                        , "sortable": True}
                     , {'field': 'area'
                        , 'title': '地区'
                        , "sortable": True}
                     , {'field': 'pe'
                        , 'title': '市盈率'
                        , "sortable": True}
                     , {'field': 'pb'
                        , 'title': '市净率'
                        , "sortable": True}
                     , {'field': 'totalAssets'
                        , 'title': '总资产(万)'
                        , "sortable": True}
                     , {'field': 'roe'
                        , 'title': 'roe'
                        , "sortable": True}                                                
                     , {'field': 'esp'
                        , 'title': '每股收益'
                        , "sortable": True}
                     , {'field': 'bvps'
                        , 'title': '每股净资'
                        , "sortable": True}
                        ]


@app.route('/get_stock_basic_json', methods=['POST', 'GET'])
def get_stock_basics_json():
    code = request.args.get("code")
    store = pd.HDFStore(app.config['FIN_TECH_HDF5'], mode='r')
#     return 'index=={0}'.format(code)
#     stock_basic = store.select('stock_basics')
    stock_basic = store.select('stock_basics_merge', where='code=="{0}"'.format(code))
    store.close()
#     return str(stock_basic.columns)

    return jsonify(stock_basic.to_dict(orient='records'))


@app.route('/get_stock_basics', methods=['POST', 'GET'])
def get_stock_basics():
    stock_basics = pd.read_hdf(app.config['FIN_TECH_HDF5'], 'stock_basics_merge', mode='r')
    stock_basics['code'] = stock_basics['code'].apply(lambda x: generate_code_html(x))   
    return render_template("table.html",
                           data=stock_basics.to_dict('record'),
                           columns=stock_basics_columns,
                           title='股票基本面')

@app.route('/table_demo', methods=['POST', 'GET'])
def get_table_demo():
    return render_template("table.html",
      data=data0,
      columns=columns0,
      title='table_demo')


# pages = FlatPages(app)

@app.route('/<path:path>/')
def page(path):
    page = pages.get_or_404(path)
    return render_template('page.html', page=page)
#     return pages.get_or_404(path).html


@app.route('/static/css/pygments.css')
def pygments_css():
    return pygments_style_defs('tango'), 200, {'Content-Type': 'text/css'}

real_data_columns = [{'field': 'code'
                      , 'title': '股票代码'
                      , "sortable": True}
                     , {'field': 'name'
                        , 'title': '股票名称'
                        , "sortable": True}
                     , {'field': 'price'
                        , 'title': '当前价格'
                        , "sortable": True}
                     , {'field': 'delta%'
                        , 'title': '波动%'
                        , "sortable": True}
                     , {'field': 'delta'
                        , 'title': '波动'
                        , "sortable": True}
                     , {'field': 'open'
                        , 'title': '今日开盘价'
                        , "sortable": True}
                     , {'field': 'pre_close'
                        , 'title': '昨日收盘价'
                        , "sortable": True}
                     , {'field': 'high'
                        , 'title': '今日最高价'
                        , "sortable": True}
                     , {'field': 'low'
                        , 'title': '今日最低价'
                        , "sortable": True}
#                      , {'field': 'date'
#                         , 'title': '日期'
#                         , "sortable": True}
#                      , {'field': 'time'
#                         , 'title': '时间'
#                         , "sortable": True}
                     , {'field': 'refresh_time'
                        , 'title': '刷新时间'
                        , "sortable": True}                      
                    ]
columns = [{'field': 'code'
                      , 'title': '股票代码'
                      , "sortable": True}
                     , {'field': 'name'
                        , 'title': '股票名称'
                        , "sortable": True}
                     , {'field': 'price'
                        , 'title': '当前价格'
                        , "sortable": True}
                     , {'field': 'delta%'
                        , 'title': '波动%'
                        , "sortable": True}
                     , {'field': 'delta'
                        , 'title': '波动'
                        , "sortable": True}
                     , {'field': 'open'
                        , 'title': '今日开盘价'
                        , "sortable": True}
                     , {'field': 'pre_close'
                        , 'title': '昨日收盘价'
                        , "sortable": True}
                     , {'field': 'high'
                        , 'title': '今日最高价'
                        , "sortable": True}
                     , {'field': 'low'
                        , 'title': '今日最低价'
                        , "sortable": True}
#                     , {'field': 'date'
#                        , 'title': '日期'
#                        , "sortable": True}
#                     , {'field': 'time'
#                        , 'title': '时间'
#                        , "sortable": True}          
                     , {'field': 'refresh_time'
                        , 'title': '刷新时间'
                        , "sortable": True}                 
                    ]

hist_data_columns = [{
    'field': 'date'
    , 'title': '日期'
    , "sortable": True}
                     , {'field': 'open'
                        , 'title': '开盘价'
                        , "sortable": True}
                     , {'field': 'close'
                        , 'title': '收盘价'
                        , "sortable": True}
                     , {'field': 'high'
                        , 'title': '最高价'
                        , "sortable": True}
                     , {'field': 'low'
                        , 'title': '最低价'
                        , "sortable": True}
                     , {'field': 'volume'
                        , 'title': '成交量'
                        , "sortable": True}
        ,{'field': 'code'
    , 'title': '股票代码'
                      , "sortable": True}
                    ]

def kline_chart(code, k_data):
    kline = Kline("{0} K 线图".format(code), width="100%")
    kline.add(("日K"), k_data['date'], k_data[['open', 'close', 'low', 'high']].values.tolist(), mark_point=["average"], is_datazoom_show=True, datazoom_xaxis_index=[0, 1])
    return kline
# [open, close, lowest, highest] 

def kline_chart_sh(sh_index_data):
    kline = Kline("上证 K 线图", width="100%", title_top="50%")
    kline.add(("日K"), sh_index_data['date'], sh_index_data[['open', 'close', 'low', 'high']].values.tolist(), mark_point=["average"], is_datazoom_show=True, datazoom_xaxis_index=[0, 1], legend_top="50%")
    return kline

@app.route('/get_realtime_data_json', methods=['GET'])
def get_realtime_data_json():
    code = request.args.get("code")
    real_data = ts.get_realtime_quotes(code)
    real_data['delta'] = (real_data['price'].astype('float') - real_data['pre_close'].astype('float'))
    real_data['delta'] = real_data['delta'].apply(lambda x: round(x, 4))
    real_data['delta%'] = real_data['delta']  / real_data['pre_close'].astype('float')
    real_data['delta%'] = real_data['delta%'].apply(lambda x: round(x*100, 2))
    real_data['refresh_time'] = str(datetime.datetime.now())
    return jsonify(real_data.to_dict(orient='records'))


# 增加一条上证走势
@app.route('/get_realtime_data', methods=['GET'])
def get_realtime_data():
    # 历史数据优先从hdf5中获取 获取不到则实时从接口获取并添加到hdf5中
    store = pd.HDFStore(app.config['STOCKS_PRICE_HDF5'], mode='r+')
    code = request.args.get("code")
#     sh_index_data = ts.get_k_data('000001', index=True)
    real_data = ts.get_realtime_quotes(code)
    if 'sh_index_data' in store:
        sh_index_data = pd.read_hdf(app.config['STOCKS_PRICE_HDF5'], 'sh_index_data', mode='r+')
    else:
        sh_index_data = ts.get_k_data('000001', index=True)
        sh_index_data.to_hdf(app.config['STOCKS_PRICE_HDF5'], 'sh_index_data', format='table', data_columns=True)
    if code in store:
        hist_data = pd.read_hdf(app.config['STOCKS_PRICE_HDF5'], code, mode='r+')
    else:
        hist_data = ts.get_k_data(code)
        hist_data.to_hdf(app.config['STOCKS_PRICE_HDF5'], code, format='table', data_columns=True)
    store.close()    
    kline = kline_chart(code, hist_data)
    # 这时还没转dict
    kline_sh = kline_chart_sh(sh_index_data)
    grid = Grid(width="100%")
    grid.add(kline, grid_bottom="60%")
    grid.add(kline_sh, grid_top="60%")
    real_data['delta'] = (real_data['price'].astype('float') - real_data['pre_close'].astype('float'))
    real_data['delta'] = real_data['delta'].apply(lambda x: round(x, 4))
    real_data['delta%'] = real_data['delta']  / real_data['pre_close'].astype('float')
    real_data['delta%'] = real_data['delta%'].apply(lambda x: round(x*100, 2))
    real_data = real_data.to_dict('record')
    hist_data = hist_data.sort_values('date', ascending=False)
    hist_data = hist_data.to_dict('record')
    return render_template("table_with_chart.html",
                           basic_data=url_for('get_stock_basics_json', code=code),
                           basic_data_columns=stock_basics_columns,                           
                           real_data=url_for('get_realtime_data_json', code=code),
                           real_data_columns=real_data_columns,
                           hist_data_columns = hist_data_columns,
                           hist_data=hist_data,
                           title=('{0}:({1})股票实时价格'.format(real_data[0]['name'], code)),
                           grid=grid.render_embed(),
                           host=app.config['REMOTE_HOST'],
                           grid_script_list=grid.get_js_dependencies(),
                          )


@app.route('/get_realtime_data_multi', methods=['GET', 'POST'])
def get_realtime_data_multi():
    update_time = str(datetime.datetime.now())
    if request.method == 'GET':
        # get需要做处理不然无法访问这个页面
        stocks=None
    else:
        stocks = request.form["stocks"]
    # return str(stocks)
    return render_template("table_with_text_area.html",
                           data=url_for('get_realtime_data_multi_json', stocks=stocks),
                           columns=columns,
                           update_time=update_time,
                           title='股票实时价格')

@app.route('/get_realtime_data_multi_json', methods=['GET'])
def get_realtime_data_multi_json():
    stocks = request.args.get("stocks")
    if stocks is None or stocks=='':
        return ''
    real_data = ts.get_realtime_quotes([s.strip() for s in stocks.split('\n')])
    real_data['code'] = real_data['code'].apply(lambda x: generate_code_html(x))   
    real_data['delta'] = (real_data['price'].astype('float') - real_data['pre_close'].astype('float'))
    real_data['delta'] = real_data['delta'].apply(lambda x: round(x, 4))
    real_data['delta%'] = real_data['delta']  / real_data['pre_close'].astype('float')
    real_data['delta%'] = real_data['delta%'].apply(lambda x: round(x*100, 2))
    real_data['refresh_time'] = str(datetime.datetime.now())        
    return jsonify(real_data.to_dict(orient='records'))

#    return '空白'

forecast_data_columns = [{'field': 'code'
                      , 'title': '股票代码'
                      , "sortable": True}
                     , {'field': 'name'
                        , 'title': '股票名称'
                        , "sortable": True}
                     , {'field': 'type'
                        , 'title': '预告类型'
                        , "sortable": True}
                     , {'field': 'report_date'
                        , 'title': '报告时间'
                        , "sortable": True}
                     , {'field': 'pre_eps'
                        , 'title': '上年同期每股收益'
                        , "sortable": True}
                     , {'field': 'range'
                        , 'title': '业绩变动范围'
                        , "sortable": True}
                        ]

@app.route('/get_forecast_data', methods=['POST', 'GET'])
def get_forecast_data():
    forecast_data = pd.read_sql_table('forecast_data', engine)
    forecast_data['code'] = forecast_data['code'].apply(lambda x: generate_code_html(x))   
    return render_template("table.html",
      data=forecast_data.to_dict('record'),
      columns=forecast_data_columns,
      title='业绩预告数据')

# 拼股票代码的html代码
def generate_code_html(code):
    code_html = url_for('get_realtime_data', code=code)
    return '<a href="{0}" target="_blank">{1}</a>'.format(code_html, code)
    


profit_pre_columns = [{'field': 'code'
                      , 'title': '股票代码'
                      , "sortable": True}
                     , {'field': 'name'
                        , 'title': '股票名称'
                        , "sortable": True}
                     , {'field': 'year'
                        , 'title': '分配年份'
                        , "sortable": True}
                     , {'field': 'report_date'
                        , 'title': '公布日期'
                        , "sortable": True}
                     , {'field': 'divi'
                        , 'title': '分红金额（每10股）'
                        , "sortable": True}
                     , {'field': 'divi_rate%'
                        , 'title': '股息率%'
                        , "sortable": True}     
                     , {'field': 'price'
                        , 'title': '最新股价'
                        , "sortable": True}                           
                     , {'field': 'shares'
                        , 'title': '转增和送股数（每10股）'
                        , "sortable": True}
                     , {'field': 'date'
                        , 'title': '日期'
                        , "sortable": True}
                     , {'field': 'time'
                        , 'title': '时间'
                        , "sortable": True}                      
                        ]

@app.route('/get_profit_pre', methods=['POST', 'GET'])
def get_profit_pre():
    profit_pre_raw = pd.read_sql_table('profit_pre', engine)
    real_price = ts.get_realtime_quotes(profit_pre_raw['code'])
    profit_pre = pd.merge(profit_pre_raw, real_price, how='left', on='code')[['code', 'name_x', 'year', 'report_date', 'divi', 'shares', 'price', 'date', 'time']]
    profit_pre.columns = ['code', 'name', 'year', 'report_date', 'divi', 'shares', 'price', 'date', 'time']
    profit_pre['price'] = profit_pre['price'].astype(float)
    profit_pre['divi_rate%'] = profit_pre['divi'] * 10 / profit_pre['price'] 
    profit_pre['divi_rate%'] = profit_pre['divi_rate%'].apply(lambda x: round(x,2))
    profit_pre['code'] = profit_pre['code'].apply(lambda x: generate_code_html(x))  
    return render_template("table.html",
      data=profit_pre.to_dict('record'),
      columns=profit_pre_columns,
      title='分红预案')

# opDate	rqchl	rqmcl	rqye	rqyl	rzche	rzmre	rzrqye	rzye	securityAbbr	stockCode	rzmre_z	rqmcl_z

margin_warning_columns = [
                        {'field': 'securityAbbr'
                        , 'title': '标的证券简称'
                        , "sortable": True}
                        ,{'field': 'industry'
                        , 'title': '所属行业'
                        , "sortable": True}
                     , {'field': 'stockCode'
                        , 'title': '标的证券代码'
                        , "sortable": True}
                    ,{'field': 'opDate'
                      , 'title': '信用交易日期'
                      , "sortable": True}
                     , {'field': 'rzye'
                        , 'title': '本日融资余额(元)'
                        , "sortable": True}
                     , {'field': 'rqyl'
                        , 'title': '本日融券余量'
                        , "sortable": True}
                     , {'field': 'rzmre_z'
                        , 'title': '本日融资买入额-z分数'
                        , "sortable": True}
                     , {'field': 'rqmcl_z'
                        , 'title': '本日融券卖出量-z分数'
                        , "sortable": True}                    
                        ]

@app.route('/get_margin_warning', methods=['POST', 'GET'])
def get_margin_warning():
    margin_warning = pd.read_sql_table('margin_warning', engine)
    margin_warning = margin_warning.sort_values(['stockCode', 'opDate'])
    margin_warning['rqmcl_z'] = margin_warning['rqmcl_z'].fillna(-1000)
    margin_warning['stockCode'] = margin_warning['stockCode'].apply(lambda x: generate_code_html(x))   
    margin_warning = margin_warning.sort_values('opDate', ascending=False)
    return render_template("table.html",
      data=margin_warning.to_dict('record'),
      columns=margin_warning_columns,
      title='两融异常')

cbond_columns = [
                        {'field': 'bcode'
                        , 'title': '转债代码'
                        , "sortable": False}
                        ,{'field': 'bname'
                        , 'title': '债券名称'
                        , "sortable": False}
                     , {'field': 'bprice'
                        , 'title': '转债价格'
                        , "sortable": True}
                     , {'field': 'cbond_value'
                        , 'title': '转股价值'
                        , "sortable": True}     
                     , {'field': 'discount_rate'
                        , 'title': '折价率%'
                        , "sortable": True}      
                     , {'field': 'sdelta%'
                        , 'title': '正股波动%'
                        , "sortable": True}              
                     , {'field': 'bdelta%'
                        , 'title': '转债波动%'
                        , "sortable": True}      
                     , {'field': 'scode'
                        , 'title': '正股代码'
                        , "sortable": False}
                    ,{'field': 'sname'
                      , 'title': '正股名称'
                      , "sortable": False}
                     , {'field': 'sprice'
                        , 'title': '正股价格'
                        , "sortable": True}      
                     , {'field': 'convprice'
                        , 'title': '转股价格'
                        , "sortable": True}
                     , {'field': 'issue_date'
                        , 'title': '上市日期'
                        , "sortable": True}
                     , {'field': 'update_time'
                        , 'title': '更新日期'
                        , "sortable": True}
                        ]

@app.route('/get_cbond_json_data', methods=['POST', 'GET'])
def get_cbond_json_data():
    cbonds = pd.read_hdf(app.config['FIN_TECH_HDF5'], 'cbonds', mode='r')
#     real_data = ts.get_realtime_quotes(list(cbonds['scode']))
#     update_time = str(datetime.datetime.now())
    real_data_stocks = ts.get_realtime_quotes(list(cbonds['scode']))
    real_data_stocks['sdelta'] = (real_data_stocks['price'].astype('float') - real_data_stocks['pre_close'].astype('float'))
    real_data_stocks['sdelta'] = real_data_stocks['sdelta'].apply(lambda x: round(x, 4))
    real_data_stocks['sdelta%'] = real_data_stocks['sdelta']  / real_data_stocks['pre_close'].astype('float')
    real_data_stocks['sdelta%'] = real_data_stocks['sdelta%'].apply(lambda x: round(x*100, 2))    
    real_data_stocks['sprice'] = real_data_stocks['price']
    cbonds['scode_raw'] = cbonds['scode'].copy()
    cbonds['scode'] = cbonds['scode'].apply(lambda x: generate_code_html(x))  
    real_data_cbonds = pd.read_hdf(app.config['FIN_TECH_HDF5'], 'cbonds_real_data', mode='r')
    real_data_cbonds['bdelta'] = (real_data_cbonds['price'].astype('float') - real_data_cbonds['last_close'].astype('float'))
    real_data_cbonds['bdelta'] = real_data_cbonds['bdelta'].apply(lambda x: round(x, 4))
    real_data_cbonds['bdelta%'] = real_data_cbonds['bdelta']  / real_data_cbonds['last_close'].astype('float')
    real_data_cbonds['bdelta%'] = real_data_cbonds['bdelta%'].apply(lambda x: round(x*100, 2))            
    real_data_cbonds['bprice'] = real_data_cbonds['price']
    data = pd.merge(cbonds[['bcode', 'bname', 'scode', 'sname', 'convprice', 'issue_date', 'scode_raw']]
                    , real_data_stocks[['code', 'sprice', 'sdelta%']]
                    , left_on='scode_raw'
                    , right_on='code')
    data = pd.merge(data[['bcode', 'bname', 'scode', 'sname', 'sprice', 'convprice', 'issue_date']]
                    , real_data_cbonds[['code', 'bprice', 'bdelta%', 'update_time']]
                    , left_on='bcode'
                    , right_on='code')    
    data['cbond_value'] = round(data['sprice'].astype(float) / data['convprice'] * 100, 2)
    data['discount_rate'] = round(((data['sprice'].astype(float) / data['convprice'] * 100 / data['bprice']) -1)*100, 2)
    data['bprice'] = data['bprice'].round(2)
    data = data.sort_values('issue_date', ascending=False)
    data['bcode'] = data['bcode'].apply(lambda x: '<a href="https://www.jisilu.cn/data/convert_bond_detail/{0}" target="_blank">{1}</a>'.format(x, x))
    return str(data.columns)
    return jsonify(data.to_dict(orient='records'))


@app.route('/get_cbond_data', methods=['POST', 'GET'])
def get_cbond_data():
    # 转债基本数据
#     url = url_for('get_cbond_json_data')
    cbonds = pd.read_hdf(app.config['FIN_TECH_HDF5'], 'cbonds', mode='r')
#     real_data = ts.get_realtime_quotes(list(cbonds['scode']))
#     update_time = str(datetime.datetime.now())
    real_data_stocks = ts.get_realtime_quotes(list(cbonds['scode']))
    real_data_stocks['sdelta'] = (real_data_stocks['price'].astype('float') - real_data_stocks['pre_close'].astype('float'))
    real_data_stocks['sdelta'] = real_data_stocks['sdelta'].apply(lambda x: round(x, 4))
    real_data_stocks['sdelta%'] = real_data_stocks['sdelta']  / real_data_stocks['pre_close'].astype('float')
    real_data_stocks['sdelta%'] = real_data_stocks['sdelta%'].apply(lambda x: round(x*100, 2))    
    real_data_stocks['sprice'] = real_data_stocks['price']
    cbonds['scode_raw'] = cbonds['scode'].copy()
    cbonds['scode'] = cbonds['scode'].apply(lambda x: generate_code_html(x))  
    real_data_cbonds = ts.get_realtime_quotes(list(cbonds['bcode']))
    real_data_cbonds['bdelta'] = (real_data_cbonds['price'].astype('float') - real_data_cbonds['pre_close'].astype('float'))
    real_data_cbonds['bdelta'] = real_data_cbonds['bdelta'].apply(lambda x: round(x, 4))
    real_data_cbonds['bdelta%'] = real_data_cbonds['bdelta']  / real_data_cbonds['pre_close'].astype('float')
    real_data_cbonds['bdelta%'] = real_data_cbonds['bdelta%'].apply(lambda x: round(x*100, 2))            
    real_data_cbonds['bprice'] = real_data_cbonds['price']
    update_time = str(datetime.datetime.now())
    real_data_cbonds['update_time'] = update_time
    data = pd.merge(cbonds[['bcode', 'bname', 'scode', 'sname', 'convprice', 'issue_date', 'scode_raw']]
                    , real_data_stocks[['code', 'sprice', 'sdelta%']]
                    , left_on='scode_raw'
                    , right_on='code')
    data = pd.merge(data[['bcode', 'bname', 'scode', 'sname', 'sprice', 'convprice', 'issue_date', 'sdelta%']]
                    , real_data_cbonds[['code', 'bprice', 'bdelta%', 'update_time']]
                    , left_on='bcode'
                    , right_on='code')    
    data['cbond_value'] = round(data['sprice'].astype(float) / data['convprice'].astype(float) * 100, 2)
    data['discount_rate'] = round(((data['sprice'].astype(float) / data['convprice'].astype(float) * 100 / data['bprice'].astype(float)) -1)*100, 2)
    data['bprice'] = data['bprice'].astype(float).round(2)
    data = data.sort_values('issue_date', ascending=False)
    data['bcode'] = data['bcode'].apply(lambda x: '<a href="https://www.jisilu.cn/data/convert_bond_detail/{0}" target="_blank">{1}</a>'.format(x, x))
    data = data.sort_values('sdelta%', ascending=False)
    data = data.to_dict(orient='records')
    return render_template("table.html",
                           data=data,
                           columns=cbond_columns,
                           title='可转债数据')

@app.route('/get_stock_similar_days', methods=['POST', 'GET'])
def get_stock_similar_days():
    #data_url='http://10.1.7.22:5000/get_es_data_hz_json?order=asc&offset=0&limit=10'
    #data = pd.read_json(data_url)
    #data_line = data.groupby('local_timestamp_new')['@timestamp'].count()    
    return '敬请期待历史上的今天'    


@app.route('/get_profile', methods=['POST', 'GET'])
def get_profile():
    name = request.args.get("username")
    if name == 'jed':
        jed_profile = {'name': 'jed', 'male': 0.85, 'female': 0.45, 'engineer': 0.65, 'artist':0.60}
        return jsonify(jed_profile)
    else:
        return '你是谁啊?'

@app.route('/get_live_data_json', methods=['POST', 'GET'])
def get_live_data_json():
    today = str(datetime.date.today())
    day = today
    data = pd.read_hdf(app.config['LIVE_DATA_HDF5'],'live_data', where='time>=pd.to_datetime("{0}")'.format(today), mode='r')
#     data = store.select('live_data')    
#     return 'ok'
    data['hour'] = data['time'].apply(lambda x: x.hour)
    data['day'] = data['time'].apply(lambda x: str(x.date()))
    data['viewers_raw'] = data['viewers'].apply(lambda x: float(x[:-1].replace(',', '')) * 10000 if '万' in x else float(x.replace(',', '')))
    data['viewers_hour'] = data['viewers_raw'] // 6
    data['url'] = data['url'].apply(lambda x: '<a href="{0}" target="_blank">{1}</a>'.format(x, x))
    group_data = data.groupby(['day', 'name','url', 'tag'])['viewers_hour'].sum()
    group_data = group_data.sort_values(ascending=False)
    return jsonify(group_data.reset_index().to_dict(orient='records'))

live_data_columns = [
                        {'field': 'day'
                        , 'title': '日期'
                        , "sortable": True}
                        ,{'field': 'name'
                        , 'title': '直播名称'
                        , "sortable": True}
                     , {'field': 'url'
                        , 'title': 'url'
                        , "sortable": True}
                    ,{'field': 'tag'
                      , 'title': 'tag'
                      , "sortable": True}
                    ,{'field': 'viewers_hour'
                      , 'title': '累积小时查看人数'
                      , "sortable": True}    
                        ]

@app.route('/get_live_data', methods=['POST', 'GET'])
def get_live_data():
    url = url_for('get_live_data_json')
    return render_template("table_json.html",
      data=url,
      columns=live_data_columns,
      title='直播网站榜单')