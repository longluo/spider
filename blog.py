#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib.request
import urllib.error
import urllib.parse

import parsel
import requests
import tomd
from bs4 import BeautifulSoup
import sqlite3

import subprocess


class Blog(object):
    def __init__(self, url):
        self.baseUrl = "http://www.longluo.me/archives/"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                          "Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75 "
        self.headers = {"User-Agent": self.user_agent}

        self.datalist2 = []

    def __del__(self):
        print('End!')

    def start(self):
        self.get_html(self.baseUrl)

        datalist, datatime, datalink = self.get_title()

        print(len(datalist))
        print(len(datatime))
        print(len(datalink))

        for i in range(0, len(datalist)):
            datalist1 = []
            datalist1.append(datalist[i])
            datalist1.append(datalink[i])

            self.datalist2.append(datalist1)

        self.get_article(self.baseUrl)
        self.get_photo()

        dbpath = 'ISHTAR.db'
        self.save_data_2_DB(dbpath)

    def get_html(self, url):
        request = urllib.request.Request(self.baseUrl, headers=self.headers)
        html = ""
        try:
            response = urllib.request.urlopen(request)
            html = response.read().decode('utf-8')
        except urllib.error.URLError as e:
            if hasattr(e, 'code'):  # 如果有错误信息，将e里的code打印出来
                print(e.code)
            if hasattr(e, "reason"):  # 如果返回对象里面有reason这个对象，就看里面的reason
                print(e.reason)
        return html

    def get_title(self):
        datalist = []
        datatime = []
        datalink = []

        findalink = re.compile('<a class="post-title-link" href="(.*)" itemprop="url">')
        for i in range(1, 15):  # for循环遍历所有页面
            finddata = re.compile('<span itemprop="name">(.*)</span>')

            if i == 1:
                findurl = self.baseUrl
            else:
                findurl = self.baseUrl + 'page/' + str(i) + '/'
            html = self.get_html(findurl)
            soap = BeautifulSoup(html, 'html.parser')  # 用html.parser来解析该html网页
            for item in soap.find_all('span', itemprop="name"):
                data = re.findall(finddata, str(item))[0]
                datalist.append(data)

            for item1 in soap.find_all('time', class_='post-time'):
                a = str(item1).find('content') + 9
                a1 = str(item1).find('"', a)
                datatime.append(str(item1)[a:a1])

            for item in soap.find_all('a', class_="post-title-link"):
                alink = re.findall(findalink, str(item))[0]
                datalink.append('http://www.longluo.me/' + alink)  # 'http://www.longluo.me/' + alink才是一个文章完整的链接

        return datalist, datatime, datalink

    def get_article(self, url):
        alinklist = []
        html = self.get_html(url)
        findalink = re.compile('<a class="post-title-link" href="(.*)" itemprop="url">')
        soap = BeautifulSoup(html, 'html.parser')
        for item in soap.find_all('a', class_="post-title-link"):
            alink = re.findall(findalink, str(item))[0]
            alinklist.append(alink)

        for i in alinklist:
            articleurl = 'http://www.longluo.me/' + i
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

    def get_photo(self):
        cmd = 'phantomjs pageload.js "%s"' % self.baseUrl
        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    def init_db(self, dbpath):  # 初始化数据库
        sql = '''
            create table RIN 
            (
            id integer primary key autoincrement,
            datetime text,
            article_info text,
            a_link text
    
            )
        '''
        conn = sqlite3.connect(dbpath)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        conn.close()

    def save_data_2_DB(self, datalist2, dbpath):  # 保存数据到数据库
        self.init_db(dbpath)
        conn = sqlite3.connect(dbpath)  # 创建数据库连接对象
        cur = conn.cursor()  # 创建游标对象

        for data in datalist2:
            for index in range(len(data)):
                data[index] = '"' + data[index] + '"'
            sql = '''
            insert into RIN(datetime, article_info, a_link)
            values (%s)''' % ",".join(data)
            cur.execute(sql)  # 执行sql语句
            conn.commit()  # 提交事务

        cur.close()
        conn.close()

def main():
    print('Please input the blog URL: eg: http://longluo.me ')
    blogUrl = input("input the blog URL:")
    blog = Blog(blogUrl)
    blog.start()

if __name__ == "__main__":
    main()
