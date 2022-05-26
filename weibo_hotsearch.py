#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import pandas as pd
from time import sleep
import numpy as np
from lxml import etree
import re
import os
import csv

class Weibo(object):
    def __init__(self):
        """初始化爬虫信息"""
        self.weiboHotUrl = 'https://s.weibo.com/top/summary?cate=realtimehot'
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"
        cookie = "SINAGLOBAL=6788372453151.379.1593919176064; _ga=GA1.2.1601691111.1602690890; UOR=,,www.baidu.com; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFosG2CxEf1L.SYPEcqN8-S5JpX5KMhUgL.FoMfSoBf1KzcShq2dJLoIp7LxKML1KBLBKnLxKqL1hnLBoMNSKqXSK.ESoBc; SSOLoginState=1653261113; _s_tentry=weibo.com; Apache=5632904354559.916.1653261124393; ULV=1653261124397:835:29:2:5632904354559.916.1653261124393:1653185715238; SCF=Ajsb1zoR2IQmauat98BKUW-CLBtWJExctPE4XBmqrc7nWVgtDoqBZVkcE-NAB9de2_dsF7sNX88GQGt9FHG5xas.; SUB=_2A25Pj0vODeRhGeFL7VYU-SzKzzqIHXVs_ToGrDV8PUNbmtAfLW6jkW9NfcDmWmhDk0PGX0xl5Jt27ZGzSG9UmKZG"
        self.headers = {"User_Agent": user_agent, "Cookie": cookie}
        self.all_df = pd.DataFrame(columns=['排行', '热度', '标题', '评论时间', '用户名称', '转发次数', '评论次数', '点赞次数', '评论内容'])
        
    def start(self):
        """运行爬虫"""
        print(self.all_df)
        self.get_hot_list()
        self.save_to_csv()

    def get_hot_list(self):
        '''
        微博热搜页面采集，获取详情页链接后，跳转进入详情页采集
        :param url: 微博热搜页链接
        :return: None
        '''
        page_text = requests.get(url=self.weiboHotUrl, headers=self.headers).text
        tree = etree.HTML(page_text)
        tr_list = tree.xpath('//*[@id="pl_top_realtimehot"]/table/tbody/tr')
        for tr in tr_list:
            parse_url = tr.xpath('./td[2]/a/@href')[0]
            detail_url = 'https://s.weibo.com' + parse_url
            title = tr.xpath('./td[2]/a/text()')[0]
            try:
                rank = tr.xpath('./td[1]/text()')[0]
                hot = tr.xpath('./td[2]/span/text()')[0]
            except:
                rank = '置顶'
                hot = '置顶'
            self.get_detail_page(detail_url, title, rank, hot)

    def get_detail_page(self, detail_url, title, rank, hot):
        '''
        根据详情页链接，解析所需页面数据，并保存到全局变量 all_df
        :param detail_url: 详情页链接
        :param title: 标题
        :param rank: 排名
        :param hot: 热度
        :return: None
        '''
        try:
            page_text = requests.get(url=detail_url, headers=self.headers).text
        except:
            return None
        tree = etree.HTML(page_text)
        result_df = pd.DataFrame(columns=np.array(self.all_df.columns))

        # 爬取3条热门评论信息
        for i in range(1, 4):
            try:
                comment_time = tree.xpath(f'//*[@id="pl_feedlist_index"]/div[4]/div[{i}]/div[2]/div[1]/div[2]/p[1]/a/text()')[0]
                comment_time = re.sub('\s','',comment_time)
                user_name = tree.xpath(f'//*[@id="pl_feedlist_index"]/div[4]/div[{i}]/div[2]/div[1]/div[2]/p[2]/@nick-name')[0]
                forward_count = tree.xpath(f'//*[@id="pl_feedlist_index"]/div[4]/div[{i}]/div[2]/div[2]/ul/li[1]/a/text()')[1]
                forward_count = forward_count.strip()
                comment_count = tree.xpath(f'//*[@id="pl_feedlist_index"]/div[4]/div[{i}]/div[2]/div[2]/ul/li[2]/a/text()')[0]
                comment_count = comment_count.strip()
                like_count = tree.xpath(f'//*[@id="pl_feedlist_index"]/div[4]/div[{i}]/div[2]/div[2]/ul/li[3]/a/button/span[2]/text()')[0]
                comment = tree.xpath(f'//*[@id="pl_feedlist_index"]/div[4]/div[{i}]/div[2]/div[1]/div[2]/p[2]//text()')
                comment = ' '.join(comment).strip()
                result_df.loc[len(result_df), :] = [rank, hot, title, comment_time, user_name, forward_count, comment_count, like_count, comment]
            except Exception as e:
                print(e)
                continue
        print(detail_url, title)
        self.all_df = self.all_df.append(result_df, ignore_index=True)        

    def save_to_csv(self):
        self.all_df.to_csv(r"weibo.csv", mode = 'a', encoding="utf-8-sig", index=False)

def main():
    wb = Weibo()
    wb.start() # 爬取微博信息

if __name__ == "__main__":
    main()   

