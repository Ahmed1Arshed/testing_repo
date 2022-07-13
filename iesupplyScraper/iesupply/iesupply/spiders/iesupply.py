import scrapy
import requests
import random
import pymongo
import pydash
import re
from rq import Queue
from redis import Redis
from pymongo import MongoClient, InsertOne
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from datetime import datetime , date
import concurrent.futures

class QuotesSpider(scrapy.Spider):
    custom_settings = {
        'RETRY_ENABLED' : True,
        'RETRY_TIMES' : 10,
        'DOWNLOAD_DELAY' : 2,
        'DOWNLOADER_MIDDLEWARES' : {
            'iesupply.middlewares.CustomRetryMiddleware': 100,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': None
        },
        'USER_AGENT': 'compitator_scraper (+http://www.yourdomain.com)',
        'DOWNLOADER_MIDDLEWARES' : {
        'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
        'scrapy_rotated_proxy.downloadmiddlewares.proxy.RotatedProxyMiddleware': 750,
        },
        'PROXY_STORAGE' : 'scrapy_rotated_proxy.extensions.file_storage.FileProxyStorage',
        'PROXY_FILE_PATH' :'/proxy_file.txt'
    }
    name = "quotes"
    start_urls = ["https://www.iesupply.com/product/detail/4111/arlington-industries-nm900"]
    
        
    def listToString(self,url):
        url_formed = ""
        for f in url: 
            url_formed += f
        return url_formed

    def parseNames(self , name):
        extracted_name = []
        nameUC = name.upper().strip()
        extracted_name.append(nameUC)
        replace = '-,_*\/|+. '
        for i in replace:
                nameUC = nameUC.replace(i , '')
        extracted_name.append(nameUC)
        nameUC = name.upper().strip()

        stringToCheck = '-R'
        if (nameUC.endswith(stringToCheck)):
            formattedName = nameUC[0:-1 * len(stringToCheck)]
            extracted_name.append(formattedName)

        stringToCheck = '-GREEN'
        if (nameUC.endswith(stringToCheck)):
            formattedName = nameUC[0:-1 * len(stringToCheck)]
            extracted_name.append(formattedName)
        
        if re.search("\\s-\\s", nameUC):
            formattedName = nameUC.split(' - ')[0]
            extracted_name.append(formattedName)
        
        return extracted_name

    def extractedNames(self , name):
        extracted_name = []
        try:
            if re.search("^DIL" , name , re.I) == None or re.findall("\\(" , name) == None:
                return self.parseNames(name)
            baseName = name.split('(')[0].strip()
            if baseName != None:
                return self.parseNames(name)
            suffixes = name.split('(').pop().split(')')[0]
            if suffixes:
                if (suffixes.includes('/')):
                    suffixes = suffixes.split('/')
                else:
                    suffixes = suffixes.split(',')
            for suffix in suffixes:
                if suffix == None:
                    return None
                baseName_formed = baseName + suffix.strip()
                extracted_name.append(self.parseNames(baseName_formed))
            return extracted_name
        except:
            return self.parseNames(name)
    def extract_unique_name(self , name):
        names = self.extractedNames(name)
        unique_list = []
        for x in names:
            if x not in unique_list:
                unique_list.append(x)
        return unique_list

    def parse(self, response):
        try:
            main_url = response.url
            main_info_details = pydash.get(response.css("div.container#contentContainer"), 0)
            if main_info_details is None:
                message = f"No main info section found for {main_url}"
                print(message)
                return
            main_details = pydash.get(response.css('div.body-content'), 0)
            if main_details is None:
                message = f"No main details section found for {main_url}"
                print(message)
                return
            main_info = pydash.get(main_details.css('div#productDetail.product'), 0)
            if main_info is None:
                message = f"No main info section found for productDetail {main_url}"
                print(message)
                return
            images = []
            img_details = pydash.get(main_info.css('div.carouselContainer') , 0)
            if img_details is not None:
                img_details_info = pydash.get(img_details.css('div.currentImage') ,0)
                if img_details_info is not None and img_details_info.css('img.primaryMedia.img-responsive'):
                    img_src = img_details_info.css("img::attr(src)").extract()
                    img_alt = img_details_info.css("img::attr(alt)").extract()
                    img_title = img_details_info.css("img::attr(title)").extract()
                    images.append({
                        "src": self.listToString(img_src),
                        "alt": self.listToString(img_alt),
                        "title": self.listToString(img_title),
                    })
            data_info = pydash.get(main_info.css('div.dataContainer') , 0)
            
            if data_info is None:
                message = f"No main info section found for dataContainer{main_url}"
                print(message)
                return
            their_name = None
            manf = ""
            data_details = pydash.get(data_info.css('div.mt10.pnInfo') ,0)
            if data_details is not None and data_details.css("span") is not None:
                all_data = data_details.css("span")
                for data in all_data:
                    if type(data.css("::text").get()) is str:
                        if (data.css("::text").get()).strip() == 'Manufacturer:':
                            manf = data.css("::text").extract()
                        if data.css("::text").get().strip() == 'Catalog #':
                            their_name = data.css("::text").extract
            offers = []
            price = None
            price_details = pydash.get(data_info.css('div.priceViewComp'), 0)
            if price_details is not None:
                price_info = pydash.get(price_details.css('div.priceContainer'), 0)
                if price_info is not None and price_info.css('span.pricerPerQty') is not None:
                    price = price_info.css('span.pricerPerQty::text').get()
                    if '$' in price or ',' in price:
                        price = price.replace('$', '').replace(',', '')

            cutsheet = ""
            cutsheet_details = pydash.get(data_info.css('div.productHighlights'), 0)
            if cutsheet_details is not None and cutsheet_details.css('span.highlight'):
                cutsheet_info = cutsheet_details.css('span.highlight')
                if cutsheet_info is not None and cutsheet_info.css("a::attr(href)"):
                    cutsheet = cutsheet_info.css("a::attr(href)")
            description = ''
            description_details = pydash.get(data_info.css('div#descContainer'), 0)
            if description_details is not None and description_details.css('div.longDesc'):
                description_info = pydash.get(description_details.css('div.longDesc') ,0)
                if description_info is not None:
                    description = description_info.extract()
            offers.append({
                "condition": "newIndBox",
                "stock": None,
                "price": {"currency": "USD", "amount": price}
            })
            extracted_name = self.extract_unique_name(their_name)
            today = date.today()
            now = datetime.now()
            d2 = today.strftime("%B %d, %Y")
            current_time = now.strftime("%H:%M:%S")
            date_time = f"{d2} {current_time}"
            scrape_object = {
                "url": main_url,
                "alternate_names": "",
                "captured_at": date_time,
                "competitor": self.name,
                "cutsheet_url": cutsheet,
                "description": description,
                "images": images,
                "long_description": description,
                "manufacturers": manf,
                "offers": offers,
                "their_name": their_name,
                "extracted_names": extracted_name,
            }
            
            yield scrape_object
        except Exception as e:
            print(e)