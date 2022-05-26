#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Todos

class Blog(object):
    def __init__(self, url):
       self.baseUrl = url
       
    def __del__(self):
        print('End!')  


def main():
    print('Please input the blog URL: eg: http://longluo.me ')
    blogUrl = input("input the blog URL:")
    blog = Blog(blogUrl)
    blog.start()

if __name__ == "__main__":
    main()   

