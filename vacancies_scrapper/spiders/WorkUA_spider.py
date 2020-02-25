import scrapy
from bs4 import BeautifulSoup
import re
import pandas as pd
import json
import csv

class WorkUASpider(scrapy.Spider):
    name = "workua"
    
    def start_requests(self):
        start_urls = [
            'https://www.work.ua/jobs/by-category/'             
        ]
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.by_category)
            # yield scrapy.Request(url=url, callback=self.by_vacancy)

    def by_category(self, response):
        categories = response.xpath('//ul[@class="cut-top text-gray-light"]//li//a')[:-4]
        for cat in categories:
            category_name = cat.xpath('./text()').get()
            category_link = cat.xpath('./@href').get()
            yield response.follow(category_link, callback=self.by_vacancy, meta={'category': category_name})
            # category_page = response.urljoin(category_link)
            # yield scrapy.Request(category_page, callback=self.by_vacancy, meta={'category': category_name})

    def by_vacancy(self, response):
        category = response.meta['category']
        for link in response.xpath('//h2[@class=""]/a/@href').getall():
            yield response.follow(link, callback=self.parse, meta={'category': category})
            # vacancy_page = response.urljoin(link)
            # yield scrapy.Request(vacancy_page, callback=self.parse)

        next_page = response.xpath('//ul[@class="pagination hidden-xs"]/li[last()]//@href').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.by_vacancy, meta={'category': category})


    def parse(self, response):
        category = response.meta['category']
        position = response.css('h1::text').get()
        salary = response.xpath('//span[@title = "Зарплата"]//following-sibling::*[1]/text()').get()
        company_info = response.xpath('//span[@title = "Дані про компанію"]//following-sibling::*//text()').getall()
        not_empty = [x.strip() for x in company_info if x.strip()]
        company_field = company_name = None
        if not_empty:
            company_name = not_empty[0]
            if len(not_empty) > 1:
                company_field = not_empty[-2]
        location = response.xpath('//span[@title = "Адреса роботи"]//following::text()').get().strip()
        cond_req = response.xpath('//span[@title = "Умови й вимоги"]//following::text()').get().strip()
        cond_req = re.sub(r'\s{2,}', '', cond_req)
        description = response.xpath('//div[@id = "job-description"]//text()').getall()
        description = '\n'.join([x.strip() for x in description if x.strip()])
        # print(description)
        vacancy =  {
                'category': category,
                'position': position,
                'salary': salary,
                'company_name': company_name,
                'company_field': company_field,
                'location': location,
                'conditions_requirments': cond_req,
                'description': description,
                'url': response.request.url

            }

        # to save all vacancies in one csv file
        # it is created once foreahead with a header vacancy.keys()

        with open('test.csv', 'a', encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=vacancy.keys())
            # writer.writeheader()
            writer.writerow(vacancy)    


      