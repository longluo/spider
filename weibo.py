#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import requests
import json
import random
from lxml import etree
from datetime import datetime
import pandas as pd

GMT_FORMAT = '%a %b %d %H:%M:%S +0800 %Y'


def crawer(page):
    agent1 = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0'
    agent2 = 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)'
    agent3 = 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)'
    agent4 = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11 '
    agent5 = 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)'

    list1 = [agent1, agent2, agent3, agent4, agent5]
    agent = random.choice(list1)

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Cookie': 'SINAGLOBAL=6788372453151.379.1593919176064; _ga=GA1.2.1601691111.1602690890; UOR=,,www.baidu.com; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFosG2CxEf1L.SYPEcqN8-S5JpX5KMhUgL.FoMfSoBf1KzcShq2dJLoIp7LxKML1KBLBKnLxKqL1hnLBoMNSKqXSK.ESoBc; SSOLoginState=1653261113; _s_tentry=weibo.com; Apache=5632904354559.916.1653261124393; ULV=1653261124397:835:29:2:5632904354559.916.1653261124393:1653185715238; SCF=Ajsb1zoR2IQmauat98BKUW-CLBtWJExctPE4XBmqrc7nWVgtDoqBZVkcE-NAB9de2_dsF7sNX88GQGt9FHG5xas.; SUB=_2A25Pj0vODeRhGeFL7VYU-SzKzzqIHXVs_ToGrDV8PUNbmtAfLW6jkW9NfcDmWmhDk0PGX0xl5Jt27ZGzSG9UmKZG',
        'User-Agent': agent
    }

    uid = '7564592646'
    page = 0
    url = 'https://m.weibo.cn/api/container/getIndex?uid={}&t=0&luicode=10000011&lfid=100103type%3D1%26q%3D%E5%9B%9B%E5%B7%9D%E6%97%A5%E6%8A%A5&type=uid&value={}&containerid=107603{}&page={}'.format(
        uid, uid, uid, page)
    print(url)
    response = requests.get(url, headers=headers)
    print(response.status_code)
    a = response.content
    ob_json = json.loads(a)
    return ob_json


pages = 3
weibo_data = []
cookie = {
    'Cookie': "_T_WM=53197759633; WEIBOCN_FROM=1110006030; XSRF-TOKEN=a2f8ba; MLOGIN=0; M_WEIBOCN_PARAMS=uicode%3D20000061%26fid%3D4493994019385691%26oid%3D4493994019385691"}
for page in range(pages):
    ob_json = crawer(page)
    if ob_json['ok'] == 1:
        list_cards = ob_json['data']['cards']
        for i in range(len(list_cards)):
            if list_cards[i]['card_type'] == 9:
                dic = {}
                mblog = list_cards[i]['mblog']
                mid = mblog['id']
                dic['微博ID'] = mid
                user = mblog['user']
                user_name = user['screen_name']
                dic['微博用户'] = user_name
                followers_count = user['followers_count']
                dic['粉丝数'] = followers_count
                is_long = mblog.get('isLongText')
                if is_long:
                    url_ = 'https://m.weibo.cn/detail/%s' % mid
                    res = requests.get(url_, cookies=cookie)
                    print(res.status_code)
                    html = res.content.decode('utf-8')
                    html = html[html.find('"status":'):]
                    html = html[:html.rfind('"hotScheme"')]
                    html = html[:html.rfind(',')]
                    html = '{' + html + '}'
                    js = json.loads(html, strict=False)
                    weibo_info = js.get('status')
                    text_body = weibo_info['text']
                    selector = etree.HTML(text_body)
                    weibo_content = etree.HTML(text_body).xpath('string(.)')
                    dic['微博内容'] = weibo_content
                else:
                    text1 = mblog['text']
                    tree = etree.HTML(text=text1)  # 过滤多于标签
                    weibo_content = tree.xpath('string(.)')
                    dic['微博内容'] = weibo_content
                created_at = mblog['created_at']  # GMT时间格式
                created_at = datetime.strptime(created_at, GMT_FORMAT)
                dic['微博发布时间'] = created_at
                weibo_data.append(dic)
    time.sleep(random.randint(5, 10))

#  weibo
weibo_df = pd.DataFrame(weibo_data)
weibo_df.to_excel("myweibo.xlsx", index=False)
