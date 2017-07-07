import pandas as pd
file = 'http://cloga.info/files/moniter_list.xlsx' # 改成你的监控文件地址
xlsx = pd.ExcelFile(file)

# 基金列表
# audit_list = ['519677', '001552', '001594', '001556', '161121']
# df = pd.read_excel(xlsx, 'Sheet1')
audit_list = pd.read_excel(xlsx, sheetname = 'fund_list', dtype={'fund_code': str})['fund_code']


# 股票列表
# equity_list = ['000166', '000002', '600369', '600016', '600000', '000651', '000538']

equity_list = pd.read_excel(xlsx, sheetname = 'equity_list', dtype={'equity_code': str})['equity_code']
# 发件smtp
from_addr = '229792471@qq.com'
# from_addr = 'cloga@163.com'
# password = raw_input('Password: ')
password = 'XXXXXX' 
# password = 'Dragon@163'
# 输入SMTP服务器地址:
# smtp_server = raw_input('SMTP server: ')
# smtp_server = 'smtp.163.com'
smtp_server = 'smtp.qq.com'


# 输入收件人地址:
# to_addr = raw_input('To: ')
to_addr = ['229792471@qq.com', '317877477@qq.com']