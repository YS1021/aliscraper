import scrapy
from scrapy.http import Request
from scrapy import Selector
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# ————————————————
# 版权声明：本文为CSDN博主「Fan_shui」的原创文章，遵循CC 4.0 BY-SA版权协议，转载请附上原文出处链接及本声明。
# 原文链接：https://blog.csdn.net/Fan_shui/article/details/81516645
import time
import re


class OSBSpider(scrapy.Spider):
    name = "osb_crawler"
    max_pages = 97
    browser = webdriver.Chrome(executable_path='/usr/local/chromedriver')

    def start_requests(self):
        url = 'https://www.alibaba.com/trade/search?fsb=y&IndexArea=product_en&CatId=&SearchText=OSB&viewtype=L&tab='
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        self.browser.get(url=response.url)
        self.browser.execute_script('window.scrollTo(0, document.documentElement.scrollHeight)')
        time.sleep(10)
        self.browser.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        
        sel = Selector(text=self.browser.page_source)
        items = sel.css('div.list-no-v2-outter.J-offer-wrapper')

        for item in items:
            rate, sales = self.get_extra(item.css('div.fc6.fs12'))
            yield {
                'name': item.css('a.elements-title-normal').xpath('@title').get(),
                # 'description': item.css('p.element-key-parameters-p::text').get() ,
                'price': item.css('span.elements-offer-price-normal__price::text').get(),
                'unit': item.css('span.elements-offer-price-normal__unit::text').get(),
                'min_order': item.css('span.element-offer-minorder-normal__value::text').get(),
                # 'seller': item.css('a.organic-gallery-offer__seller-company').xpath('@title').get(),
                'response_rate': rate,
                'sales': sales,
                'seller': item.css('a.fc3.fs12::text').get(),
                'seller_year': item.css('span.seller-tag__year::text').get(),
                'seller_level': self.get_level(item.css('i.iconfont.iconzuanshi.seller-star-level__dm').xpath('@class').getall()),
                
            }

        # Pagination
        if '&page=' not in response.url and self.max_pages >= 2:
            yield Request(response.request.url + "&page=2")
        else:
            url = response.request.url
            current_page_no = re.findall('page=(\d+)', url)[0]
            next_page_no = int(current_page_no) + 1
            url = re.sub('(^.*?&page\=)(\d+)(.*$)', rf"\g<1>{next_page_no}\g<3>", url)
            if next_page_no <= self.max_pages:
                yield Request(url, callback=self.parse)


    def get_extra(self, s):
        # s = item.css('div.fc6.fs12')
        rate = ''
        sales = ''
        text_list = s.css('::text').getall()
        if len(text_list) == 4:
            rate = text_list[0]
            sales = ' '.join(text_list[2:])
        elif len(text_list) == 2:
            if 'Response' == text_list[1]:
                rate = text_list[0]
            else:
                sales = ' '.join(text_list)

        return [rate, sales]

    def get_level(self, dms):
        org_dm = 0
        grey_dm = 0
        for dm in dms:
            if 'orange' in dm:
                org_dm += 1
            else:
                grey_dm += 1
        return str(org_dm) + ' orange dimond(s), ' + str(grey_dm) + ' grey dimond(s)'
