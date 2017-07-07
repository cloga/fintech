# -*- coding: utf-8 -*-  
import tushare as ts
import pandas as pd 
import requests
from bs4 import BeautifulSoup
import re
import datetime
from functools import reduce
from config import audit_list, equity_list
from data_fetcher import get_fund_histdata, get_fund_currdata, get_hist_raw_data_equity

now_time = datetime.datetime.now()


