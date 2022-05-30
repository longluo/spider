#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging.config
import os
import re
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

        self.data = pd.DataFrame(columns=['id', 'title', 'create_date', 'article_link'])

        logger.info(self.baseUrl + " , " + self.archivesUrl)

    def __del__(self):
        print('End!')

    def start(self):
        self.get_html(self.archivesUrl)

        datalist, datatime, datalink = self.get_page()

        result_data = pd.DataFrame(columns=np.array(self.data.columns))

        for i in range(0, len(datalist)):
            uid = i + 1
            title = datalist[i]
            create_date = ""
            article_link = datalink[i]

            # logger.info(uid + "," + title + "," + create_date + "," + article_link)
            result_data.loc[len(result_data), :] = [uid, title, create_date, article_link]

            self.data = self.data.append(result_data, ignore_index=True)
            self.save_to_csv()

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

    def get_page(self):
        data_list = []
        data_time = []
        data_link = []

        article_link = re.compile('<a class="post-title-link" href="(.*)" itemprop="url">')

        logger.info(article_link)

        # total_pages = re.compile('<span class="space">&hellip;</span><a class="page-number" href="(.*)">(.*)</a>')

        for i in range(1, 2):

            finddata = re.compile('<span itemprop="name">(.*)</span>')

            if i == 1:
                findurl = self.archivesUrl
            else:
                findurl = self.baseUrl + '/page/' + str(i) + '/'

            logger.info(finddata)
            logger.info(findurl)

            html = self.get_html(findurl)

            soap = BeautifulSoup(html, 'html.parser')  # 用html.parser来解析该html网页

            for item in soap.find_all('span', itemprop="name"):
                data = re.findall(finddata, str(item))[0]
                data_list.append(data)

            for item1 in soap.find_all('time', class_='post-time'):
                a = str(item1).find('content') + 9
                a1 = str(item1).find('"', a)
                data_time.append(str(item1)[a:a1])

            for item in soap.find_all('a', class_="post-title-link"):
                alink = re.findall(article_link, str(item))[0]
                data_link.append(self.baseUrl + alink)

        return data_list, data_time, data_link

    def save_to_csv(self):
        self.data.to_csv(r"blog.csv", mode='a', encoding="utf-8-sig", index=False)

    def get_article(self, url):
        alinklist = []
        html = self.get_html(url)
        findalink = re.compile('<a class="post-title-link" href="(.*)" itemprop="url">')
        soap = BeautifulSoup(html, 'html.parser')
        for item in soap.find_all('a', class_="post-title-link"):
            alink = re.findall(findalink, str(item))[0]
            alinklist.append(alink)

        for i in alinklist:
            articleurl = self.baseUrl + i
            print(articleurl)
            response = requests.get(articleurl)
            html = response.text
            sel = parsel.Selector(html)
            content = sel.css('article').get()
            text = tomd.Tomd(content).markdown
            print(text)
            with open('pc.md', mode='a', encoding='utf-8', )as f:
                f.write(text)
                f.close()


def main():
    print('Please input the blog URL: eg: http://longluo.me ')
    # siteUrl = input("input the blog URL:")
    siteUrl = "http://www.longluo.me"
    blog = Blog(siteUrl)
    blog.start()


if __name__ == "__main__":
    main()
