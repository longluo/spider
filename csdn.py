import math
from http import cookiejar
import re
from bs4 import BeautifulSoup
import pdfkit
import time
import random
import os
import sqlite3
import multiprocessing
import threading
from PyPDF2 import PdfFileReader, PdfFileWriter
import sys
import io
import requests


class CSDN(object):
    def __init__(self, username):
        super(CSDN, self).__init__()

        self.username = username
        self.baseUrl = 'https://blog.csdn.net/%s/article/list/' % username;

        self.conn = sqlite3.connect('csdn.db')
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS %s( 
            id         INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            url        TEXT,
            title      TEXT,
            srcHtml    BLOB
            ) 
            ''' % self.username)

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS %s_Index( 
            id         INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            url        TEXT,
            indexHtml    BLOB
            ) 
            ''' % self.username)

        self.articleNumber = 0
        self.merge = PdfFileWriter()
        self.catlogPageNum = 0

    def __del__(self):
        print('结束了')
        self.conn.commit()
        self.conn.close()

    def insert2Db(self, url, title, srcHtml, cleanedHtml):
        print(url)
        self.cursor.execute(
            '''select count(*) from "%s" where url = "%s"''' % (self.username, url))
        if not self.cursor.fetchone()[0]:
            self.cursor.execute('INSERT INTO %s (url, title, srcHtml)  VALUES (?,?,?)' % (
                self.username,), (url, title, memoryview(srcHtml.encode(encoding="utf-8"))))

    def getArticleByUrl(self, url, articleName):
        while True:
            try:
	            headers = {
	            	#'Cookie': 'acw_tc=2760821915709055383842117e5e11fa015afba4a726c9740ff1e10d94aadd; acw_sc__v2=5da21e15ffe8d6436eac8909c7893531a38a3f55; uuid_tt_dd=10_18796629400-1570905623613-532111; dc_session_id=10_1570905623613.376716; Hm_lvt_6bcd52f51e9b3dce32bec4a3997715ac=1570905624; Hm_ct_6bcd52f51e9b3dce32bec4a3997715ac=6525*1*10_18796629400-1570905623613-532111; dc_tos=pz9yv1; Hm_lpvt_6bcd52f51e9b3dce32bec4a3997715ac=1570906046',
	            	"Accept-Encoding": "gzip, deflate, br",
	            	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
	            	'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6,es;q=0.5,sv;q=0.4,da;q=0.3,la;q=0.2,fr;q=0.1,su;q=0.1,de;q=0.1,pt;q=0.1,cy;q=0.1,ca;q=0.1,mt;q=0.1,nl;q=0.1,nb;q=0.1,lb;q=0.1,mr;q=0.1',
	            	'Host': 'blog.csdn.net',
	    			'Connection': 'keep-alive',
	    			'Sec-Fetch-Mode': 'navigate',
	    			'Sec-Fetch-User': '?1',
	    			'Upgrade-Insecure-Requests': '1',
	                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
	            }

	            response = requests.get(url)

	            headers['Cookie'] = 'acw_sc__v2=5da21e15ffe8d6436eac8909c7893531a38a3f55;'
	            response = requests.get(url, headers=headers)
	            print(response.content)

	            
	   
	            break
            except:
               print("获取 <%s> 时,发生故障! %s\n" % (articleName, url))
               time.sleep(random.randint(5, 10))

        data = response.text

        return data

    def getArticlesInPage(self, html):
        soup = BeautifulSoup(html, "lxml")

        articleList = soup.find(
            class_='article-list').find_all(class_='article-item-box')

        for article in articleList:
            # 这里竟然反爬虫
            if article.has_attr('style') and u'display: none;' == article['style']:
                print('贱人竟然如此绝招')
                continue
            article = article.find('a')

            href = article.get('href')
            title = article.get_text("|", strip=True)[2:]

            #print('链接:%s, 标题: %s' % (href, title))
            self.cursor.execute(
                '''select count(*) from "%s" where url = "%s"''' % (self.username, href))
            if not self.cursor.fetchone()[0]:
                srcHtml = self.getArticleByUrl(href, title)
                cleanedData = ''
                self.insert2Db(href, title, srcHtml, cleanedData)
            else:
                print('文章"%s"已经存在' % (title, ))
                pass

    def getPageByIndex(self, pageIndex):
        url = self.baseUrl + str(pageIndex)
        print('准备获取目录页面' + url)
        self.cursor.execute(
            '''select count(*) from "%s_Index" where url = "%s"''' % (self.username, url))
        if self.cursor.fetchone()[0]:
            print("爬过了%s" % url)
            return True

        # headers = {
        #     'Host': 'blog.csdn.net',
        #     'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
        # }

        # request = urllib.request.Request(url=url, headers=headers, method='GET')
        # response = self.opener.open(request)
        # print(response)
        # html = response.read().decode('utf-8');
        #html = html.decode('utf-8');

        while True:
            try:
                #html = request.urlopen(url).read().decode('utf-8')
                html = requests.get(url).text
                break
            except:
                print("当前第%d页,发生故障!\n" % pageIndex)
                time.sleep(5)

        soup = BeautifulSoup(html, "lxml")
        #print(soup.prettify())

        if html.find('class="no-data') != -1 and html.find('<h6>空空如也</h6>') != -1:
            return False
        else:

            self.cursor.execute('INSERT INTO %s_Index (url, indexHtml)  VALUES (?,?)' % (
                self.username,), (url, memoryview(html.encode(encoding="utf-8"))))

            self.getArticlesInPage(html)
            return True

    def cleanHtmlData(self, html, id):
        cleanedData = ''
        soup = BeautifulSoup(html, "lxml")
        blog_content_box = soup.find(class_='blog-content-box')

        cleanedData += '''
            <!DOCTYPE html>
            <html lang="zh-CN">
                <head>
                    <meta charset="UTF-8">
                    %s
                <link rel="stylesheet" href="https://csdnimg.cn/release/phoenix/template/css/detail-60a2c245da.min.css">
                <link rel="stylesheet" href="https://csdnimg.cn/release/phoenix/themes/skin3-template/skin3-template-88717cedf2.min.css">
                <script type="text/javascript">
                var username = "";
                </script>
                <script src="https://csdnimg.cn/public/common/libs/jquery/jquery-1.9.1.min.js" type="text/javascript"></script>
                <!-- 新版上报 -->
                <!-- 新版上报end -->
                <link rel="stylesheet" href="https://csdnimg.cn/public/sandalstrap/1.3/css/sandalstrap.min.css"> 
                </head>
                <body>    
        
                    <link rel="stylesheet" href="https://csdnimg.cn/release/phoenix/template/css/blog_code-c3a0c33d5c.css">
                    <div class="container clearfix pt0" id="mainBox">
        ''' % (soup.title.prettify())

        cleanedData += '<main style="width: 100%;">'
        cleanedData += blog_content_box.prettify()
        # cleanedData += article_title_box.prettify()
        # cleanedData += article_info_box.prettify()
        # cleanedData += article_content.prettify()
        # cleanedData += article_bar_bottom.prettify()
        cleanedData += '''<div class="recommend-box">
                            <div style="background: #fff; border: dashed 1px #666; padding-left: 1em; padding-top: 1em; padding-bottom: 1em;">
                                <span style="font-size: 0.8em; font-weight: bold;">
                                    此PDF由<a style="color:#0000ff" href="http://www.github.com/spygg"  target="_blank">spygg</a>生成,请尊重原作者版权!!!
                                    <br/>
                                    我的邮箱:liushidc@163.com
                                </span>
                                </div> 
                        </div>
                    </main>
      
                </div>
            <script>
                var recommendCount = 0;
                var articleTit = "";
                var articleId = "";
                var commentscount = 0;
                //1禁止评论，2正常
                var commentAuth = 1;
                //百度搜索
                var baiduKey = "";
                var needInsertBaidu = "";
            </script>
            <script src="https://csdnimg.cn/release/phoenix/template/js/detail-effe72036e.min.js"></script>
            </body>
        </html>'''

        cleanedData = cleanedData.replace(
            'class="hide-article-box', 'style="display:none;" class="hide-article-box')
        cleanedData = cleanedData.replace('class="float-right', '')
        # 生成锚链接
        cleanedData = cleanedData.replace(
            'class="article-title-box"', 'class="article-title-box" id="article_anchors_%d"' % (id))

        # 修复图片索引错误
        cleanedData = cleanedData.replace(
            'src="//img-blog.csdn.net', 'src="https://img-blog.csdn.net')

        if not os.path.exists('html'):
            os.mkdir('html')
        # 修复windows下编码错误
        with open('html/%d.html' % id, "w", encoding='utf-8') as f:
            f.write(cleanedData)
        return cleanedData

    def doConvert(self, id, html, forceUpdate=False):
        #pdfkit.from_file("dhtml/%s.html" % fileName, 'pdf/%s.pdf' % fileName)
        if not os.path.exists('pdf'):
            os.mkdir('pdf')

        if forceUpdate or (not os.path.exists('pdf/%d.pdf' % id)):
            print("正在生成第%d篇pdf (%d of %d)" % (id, id, self.articleNumber))
            ts = 0
            while True:
                # 获取输出结果
                ts = ts + 1

                if ts > 5:
                    print('5次失败后, 放弃获取图片')
                    break

                # c重定向输出结果
                stdout = sys.stdout
                err = io.StringIO()
                sys.stdout = err
                pdfkit.from_string(html, 'pdf/%d.pdf' % id)

                # 恢复重定向
                sys.stdout = stdout

                r = err.getvalue()

                print(r)
                if r.find('Warning: Failed to load') == -1:
                    break
                else:
                    #print("生成%d篇文章pdf时发生意外,重试中...." % id)
                    pass

    def doMerge(self):
        print("PDF生成完成, 开始合并........")
        pageIndex = 0
        for i in range(0, self.articleNumber):
            # 倒叙排列
            pdf = PdfFileReader(open('pdf/%d.pdf' %
                                     (self.articleNumber - i), "rb"))

            pageCount = pdf.getNumPages()
            # title = pdf.getDocumentInfo().title.replace(' - CSDN博客', '')

            # if not title:
            title = ""
            self.cursor.execute(
                'select title from %s where id = %d' % (self.username, (self.articleNumber - i)))
            result = self.cursor.fetchall()

            for r in result:
                title = r[0]
                # print('为空, 从新获取%s %s' % (result, title))
                break

            if not title:
                title = "博客目录"

            #print(title, pageCount)
            self.merge.appendPagesFromReader(pdf)
            self.merge.addBookmark(title, pageIndex)
            pageIndex += pageCount

        # 设置最大递归深度,不然报错
        sys.setrecursionlimit(5000)
        self.merge.write(open("%s.pdf" % self.username, "wb"))
        sys.setrecursionlimit(1000)

    def calcDotNum(self, begin, end):
        line = ''
        size = 1024

    def generateCatlog(self, forceUpdate=False):

        if not forceUpdate:
            print('正在生成目录....')
        else:
            print("正在更新目录页码!")

        articleIndex = 1
        pageIndex = 0

        pdfcontent = ''
        pdfcontent = pdfcontent + '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>博客目录</title></head><body><div style='font-size:30px;text-align:center;'> 目录 </div>'''

        for i in range(0, self.articleNumber):
            pdf = PdfFileReader(open('pdf/%d.pdf' %
                                     (self.articleNumber - i), "rb"))
            pageCount = pdf.getNumPages()
            # title = pdf.getDocumentInfo().title.replace(' - CSDN博客', '')
            # print(pdf.getDocumentInfo())

            title = ""
            # 修复标题为空的bug
            # if not title:
            self.cursor.execute(
                'select title from %s where id = %d' % (self.username, self.articleNumber - i))
            result = self.cursor.fetchall()

            for r in result:
                title = r[0]
                #print('为空, 从新获取%s %s' % (result, title))
                break

            # #目录..........................................

            pdfcontent = pdfcontent + '''
                            <div style="max-width:100%;line-height:1.8em;margin-top:5px;background-color:#ccc;">
                            <span class="start">
                        '''

            # 序号,标题
            pdfcontent = pdfcontent + \
                '''%d.<a href='javascript:{document.getElementById("article_anchors_%d").scrollIntoView()};'>%s</a></span>''' % (
                    articleIndex, articleIndex, title)
            pdfcontent = pdfcontent + \
                '''<span class='middle' style="max-height:25px;overflow:hidden;display:inline-block"></span>'''
            pdfcontent = pdfcontent + ''' <span class="end" style="float:right;">'''
            # 页码.....
            pdfcontent = pdfcontent + \
                '%d' % (pageIndex + 1 + self.catlogPageNum)
            pdfcontent = pdfcontent + '</span></div>'

            articleIndex = articleIndex + 1
            pageIndex += pageCount

        pdfcontent = pdfcontent + '</body></html>'

        if not os.path.exists('html'):
            os.mkdir('html')

        with open('catlog.html', "w") as f:
            f.write(pdfcontent)

        if forceUpdate:
            self.articleNumber = self.articleNumber + 1

        if not forceUpdate:
            self.doConvert(self.articleNumber + 1, pdfcontent, True)
        else:
            self.doConvert(self.articleNumber, pdfcontent, True)

        # 获取目录页码
        if forceUpdate:
            print('目录生成完成....')

    def generateCatlogAndUpdate(self):
        # 第一次生成目录
        self.generateCatlog()

        pdf = PdfFileReader(open('pdf/%d.pdf' %
                                 (self.articleNumber + 1), "rb"))
        self.catlogPageNum = pdf.getNumPages()

        # 重新生成目录
        self.generateCatlog(True)

    def startThreadPool(self):
        processList = []

        # 降序排列
        self.cursor.execute('select id, srcHtml from %s' % (self.username))

        result = self.cursor.fetchall()
        self.articleNumber = len(result)
        print("一共 %d篇文章, 准备生成PDF文件...." % self.articleNumber)

        for (id, srcHtml) in result:
            #process = multiprocessing.Process(target = self.doConvert, args = (id, cleanedHtml))
            if not os.path.exists('pdf/%d.pdf' % id):
                cleanedHtml = self.cleanHtmlData(srcHtml.decode('utf-8'), id)

                process = threading.Thread(
                    target=self.doConvert, args=(id, cleanedHtml))
                processList.append(process)

        k = 0
        while k < len(processList):
            temProcessList = []
            for i in range(0, 30):
                processList[k].start()
                temProcessList.append(processList[k])
                #print('启动%d' % k)
                k = k + 1
                if k >= len(processList):
                    break

            for tmpProcess in temProcessList:
                tmpProcess.join()


if __name__ == '__main__':
    #username = 'tcpipstack'
    print('先输入用户名:如https://blog.csdn.net/spygg 则输入spygg')
    username = input("input user's name: ")
    csdn = CSDN(username)

    print('开始获取文章列表.....')
    i = 1
    
    while(True):
        pageNumber = csdn.getPageByIndex(i)

        if pageNumber:
            pass
        else:
            break

        break
        i = i + 1

    print('索引页获取完成, 共 %d 页!!!' % (i - 1))

    csdn.startThreadPool()
    csdn.generateCatlogAndUpdate()
    csdn.doMerge()
