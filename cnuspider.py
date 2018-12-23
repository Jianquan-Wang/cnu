# -*- coding: utf-8 -*-

from selenium import webdriver
from lxml import etree
import os
import requests
import time
import random
import json


class CnuSpider(object):
    '''
    CNU作者作品爬取
    需提供作者页面的链接
    有日志文件，可以判断有没有已经下载
    '''

    def __init__(self):
        # 图片保存目录
        self.download_path = os.getcwd() + "\download"
        if not os.path.exists(self.download_path):
            os.mkdir(self.download_path)

        chrome_options = webdriver.ChromeOptions()
        # 开启无界面模式
        chrome_options.headless = False
        self.browser = webdriver.Chrome(options=chrome_options)

        # 图片路径的开头部分
        self.imgUrl = 'http://img.cnu.cc/uploads/images/920/'

    def checkIsDownloadAndWrite(self, url):
        '''检查文件名是否存在和链接是否已经在文件中'''
        if not os.path.isfile('download_log.txt'):
            with open('download_log.txt', 'w') as f:
                f.write("")
            return False
        else:
            with open('download_log.txt', encoding='utf-8') as f:
                if url in f.read().split('\n'):
                    return True
                else:
                    return False

    def getInfoUrl(self, url):
        '''获取页面的全部作品地址'''
        try:
            self.browser.get(url)

            # 判断链接是否已经下载过
            if not self.checkIsDownloadAndWrite(url):
                self.writeLog(url)
            else:
                print("该链接已经下载，请输入新链接")
                return

            pageTitle = self.browser.find_element_by_class_name('page-title').text
            print('---', pageTitle)
        except:
            print("*****程序出错，请检查链接是否正确*****")

        try:
            # 查看是否出现了分页栏，异常就为出现，否则反之
            self.browser.find_element_by_class_name('pagination')
        except:
            # 睡眠,防止封了IP
            time.sleep(round(random.uniform(1, 4), 2))
            self.parseInfoUrl(url)
        else:
            # 出现分页栏
            html = etree.HTML(self.browser.page_source)
            pages = html.xpath('//div[@class="pager_box"]/ul/li/a/text()')
            # 判断分页栏出现的个数
            if len(pages) == 2:
                page = 2
            else:
                page = int(pages[-2])
            # 生成url链接
            for n in range(1, page + 1):
                baseUrl = url.split('?page=')[0] + '?page=' + str(n)
                self.parseInfoUrl(baseUrl)

        print('\r\n--- 全部下载成功')

    def writeLog(self, url):
        '''下载页面的记录保存'''
        # 域名和作者文件名
        author_name = self.browser.find_element_by_class_name('author_name').text
        self.authorPath = os.path.join(self.download_path, author_name)
        if not os.path.exists(self.authorPath):
            os.mkdir(self.authorPath)

        # 写入下载日记文件
        with open('download_log.txt', 'a', encoding='utf-8') as f:
            f.write(url)
            f.write('\n')
            f.write(author_name)
            f.write('\n\n')

    def parseInfoUrl(self, url):
        '''处理每个作品的url'''
        self.browser.get(url)
        # xpath匹配
        html = etree.HTML(self.browser.page_source)
        imgUrls = html.xpath('//*[@id="recommendForm"]/div')
        # 判断有无匹配到信息
        if len(imgUrls):
            for url in imgUrls:
                title = url.xpath('./a/div[1]/text()')
                work = url.xpath('./a/@href')[0]
                if not len(title):
                    title = time.strftime('%Y%m%d_%H%M%S')
                else:
                    title = title[0].strip()
                self.getImgsUrl(title, work)
        else:
            print("没有匹配到具体作品信息的链接")

    def getImgsUrl(self, title, work):
        '''获取页面中照片的地址'''
        # 睡眠,防止封了IP
        time.sleep(round(random.uniform(1, 4), 2))
        self.browser.get(work)
        # 执行JS脚本, 把下拉菜单拉到最底部
        self.browser.execute_script('window.scrollTo(0,document.body.scrollHeight)')
        srcAddress = self.browser.find_element_by_id('imgs_json').get_attribute('textContent')

        srcs = []
        for i in json.loads(srcAddress):
            src = self.imgUrl + i['img']
            srcs.append(src)

        print(srcs)

        # 文件名处理
        titleName = self.replaceUrl(title)

        # 文件路径
        addr = os.path.join(self.authorPath, titleName)
        if not os.path.exists(addr):
            os.mkdir(addr)

        # 网页链接
        url_path = os.path.join(addr, 'url.txt')
        with open(url_path, 'w', encoding='utf-8') as f:
            f.write(work)

        for src in srcs:
            self.getImgAndWrite(addr, src)

    def replaceUrl(self, name):
        '''替换名称中出现的不正常字符'''
        if name == '/' or name == 'Untitled' or name == '／':
            name = time.strftime('%Y-%m-%d %H-%M-%S')
        name = name.replace('/', '-')
        name = name.replace('\\', '-')
        name = name.replace(':', '-')
        name = name.replace('*', '-')
        name = name.replace('?', '-')
        name = name.replace('<', '-')
        name = name.replace('>', '-')
        name = name.replace('|', '-')
        name = name.replace('"', '-')
        return name

    def getImgAndWrite(self, addr, src):
        '''获取图片的字节和保存图片'''
        # 保存图片的地址
        imgName = src.split('/')[-1]
        imgPath = os.path.join(addr, imgName)
        # 睡眠,防止封了IP
        time.sleep(round(random.uniform(1, 3), 2))
        # 获取图片的字节
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;'}
        res = requests.get(src, headers=headers)
        res.encoding = 'utf-8'
        img = res.content

        # 写入文件夹
        with open(imgPath, 'wb') as f:
            f.write(img)

        print(imgPath, src, " 下载成功...")

    def workOn(self, url):
        '''主程序'''
        print('\n开始进入', url, '...')
        self.getInfoUrl(url)
        # 浏览器退出
        self.browser.quit()


if __name__ == '__main__':
    # 作者作品链接
    urls = [
        'http://www.cnu.cc/users/511962',
        'http://www.cnu.cc/users/121692',
        'http://www.cnu.cc/users/254034',
        'http://www.cnu.cc/users/295337',
        'http://www.cnu.cc/users/132431',
        'http://www.cnu.cc/users/118423',
        'http://www.cnu.cc/users/129929',
        'http://www.cnu.cc/users/227614',
        'http://www.cnu.cc/users/147960',
        'http://www.cnu.cc/users/119867',
        'http://www.cnu.cc/users/129239',
        'http://www.cnu.cc/users/129358',
        'http://www.cnu.cc/users/106718',
        'http://www.cnu.cc/users/106718',
        'http://www.cnu.cc/users/364430',
    ]
    # url = 'http://www.cnu.cc/users/4885962'
    for url in urls:
        spider = CnuSpider()
        spider.workOn(url)
