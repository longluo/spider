#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging.config
import os
import re
import sqlite3
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import warnings

import numpy as np
import pandas as pd
import parsel
import requests
import tomd
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore")

# 如果日志文件夹不存在，则创建
if not os.path.isdir("log/"):
    os.makedirs("log/")
logging_path = os.path.split(os.path.realpath(__file__))[0] + os.sep + "logging.conf"
logging.config.fileConfig(logging_path)
logger = logging.getLogger("blog")


class Blog(object):
    def __init__(self, url):
        self.baseUrl = url
        self.archivesUrl = self.baseUrl + "/archives"

        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                          "Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75 "
        self.headers = {"User-Agent": self.user_agent}

        self.total_pages = 1

        self.posts_data = pd.DataFrame(columns=['id', 'title', 'create_date', 'article_link'])

        self.db_path = 'blog.db'

    def __del__(self):
        print('End!')

    def start(self):
        # self.total_pages = self.get_total_page()
        self.total_pages = 2

        data_list, data_time, data_link = self.get_page()
        result_data = pd.DataFrame(columns=np.array(self.posts_data.columns))

        for i in range(0, len(data_list)):
            uid = i + 1
            title = data_list[i]
            create_date = data_time[i]
            article_link = data_link[i]

            result_data.loc[len(result_data), :] = [uid, title, create_date, article_link]
            self.posts_data = self.posts_data.append(result_data, ignore_index=False)
            logger.info(str(uid) + " " + title + " " + create_date + " " + article_link)

        for i in range(0, len(data_link)):
            self.get_article(data_link[i])

        self.save_to_csv()
        self.save_data_2_db()

    def get_html(self, url):
        request = urllib.request.Request(url, headers=self.headers)

        html = ""

        try:
            response = urllib.request.urlopen(request)
            html = response.read().decode('utf-8')
        except urllib.error.URLError as e:
            if hasattr(e, 'code'):
                logger.error(e.code)
            if hasattr(e, "reason"):
                logger.error(e.reason)

        return html

    def get_total_page(self):
        html = self.get_html(self.archivesUrl)

        page_number = re.compile('[0-9]+')

        soap = BeautifulSoup(html, 'html.parser')

        page_item = soap.find_all('a', class_="page-number")
        total_pages = re.findall(page_number, str(page_item))[-1]
        return int(total_pages)

    def get_page(self):
        data_list = []
        data_date = []
        data_link = []

        page_post_link = re.compile('<a class="post-title-link" href="(.*)" itemprop="url">')

        for i in range(1, self.total_pages):
            page_post_title = re.compile('<span itemprop="name">(.*)</span>')
            page_post_date = re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2}')

            if i == 1:
                page_url = self.archivesUrl
            else:
                page_url = self.archivesUrl + '/page/' + str(i) + '/'

            html = self.get_html(page_url)

            soap = BeautifulSoup(html, 'html.parser')  # 用html.parser来解析该html网页

            for title_item in soap.find_all('span', itemprop="name"):
                post_title = re.findall(page_post_title, str(title_item))[0]
                data_list.append(post_title)

            for date_item in soap.find_all('time', itemprop='dateCreated'):
                post_date = re.findall(page_post_date, str(date_item))[0]
                data_date.append(post_date)

            for link_item in soap.find_all('a', class_="post-title-link"):
                post_link = re.findall(page_post_link, str(link_item))[0]
                data_link.append(self.baseUrl + post_link)

        return data_list, data_date, data_link

    def save_to_csv(self):
        self.posts_data.to_csv(r"blog.csv", mode='w', encoding="utf-8-sig", index=False)

    def get_article(self, url):
        response = requests.get(url)

        html = response.text

        selector = parsel.Selector(html)

        content = selector.css('article').get()

        text = tomd.Tomd(content).markdown

        with open('pc.md', mode='a', encoding='utf-8', )as f:
            f.write(text)
            f.close()

    def get_photo(self):
        cmd = 'phantomjs pageload.js "%s"' % self.baseUrl
        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    def init_db(self, dbpath):  # 初始化数据库
        sql = """
            create table RIN 
            (
            id integer primary key autoincrement,
            article_title text,
            create_date text,
            article_link text
            )
        """
        conn = sqlite3.connect(dbpath)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        conn.close()

    def save_data_2_db(self):  # 保存数据到数据库
        self.init_db(self.db_path)
        conn = sqlite3.connect(self.db_path)  # 创建数据库连接对象
        cur = conn.cursor()  # 创建游标对象

        for item in self.posts_data:
            sql = """
                insert into RIN(article_title, create_date, article_link)
                values (%s)""" % ",".join(item)
            cur.execute(sql)  # 执行sql语句
            conn.commit()  # 提交事务

        cur.close()
        conn.close()


def main():
    print('Please input the blog URL: eg: http://longluo.me ')
    # siteUrl = input("input the blog URL:")
    siteUrl = "http://www.longluo.me"
    blog = Blog(siteUrl)
    blog.start()


if __name__ == "__main__":
    main()
