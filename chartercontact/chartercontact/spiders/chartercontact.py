import scrapy
import requests
import random
import pymongo
from rq import Queue
from redis import Redis
from pymongo import MongoClient, InsertOne
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from datetime import datetime , date
import re
import pydash
class QuotesSpider(scrapy.Spider):
    name = "quotes"
    start_urls = ["https://www.chartercontact.com/6-288"]
    
    def multithreading(self):
        q = Queue(connection=Redis())
        result = q.enqueue(self.setting_proxy, self, self.start_urls)
    def listToString(self,url):
        url_formed = ""
        for f in url: 
            url_formed += f
        return url_formed
    def setting_proxy(self,start_urls):
        software_names = [SoftwareName.CHROME.value]
        operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
        user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)
        user_agent = user_agent_rotator.get_random_user_agent()
        headers =  {
            'Accept': '*/*',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'User-Agent': user_agent,
            'X-Requested-With': 'XMLHttpRequest'
        }
        csv_url = "https://blazingseollc.com/proxy/dashboard/api/export/4/all/winston@widespread.com/y4ckhBal/list.csv"
        req = requests.get(csv_url)
        url_content = req.content
        url_content = url_content.decode()
        url = url_content.split("\n")
        random_url = random.choice(url)
        random_url = random_url.split(":")
        rand_url = 'http://'+random_url[2] +':'+ random_url[3] + '@' + random_url[0] +":"+ random_url[1]
        request = scrapy.Request(url=self.listToString(start_urls),method='GET', headers= headers , callback=self.parse)
        request.meta['proxy'] = rand_url
        request.meta['tunnel'] = True
        yield request

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
            main_info = pydash.get(response.css("div#ProductSection"), 0)
            if main_info is None:
                message = f"No main info section found for {main_url}"
                print(message)
                return
            main_details = pydash.get(main_info.css("div.grid"), 0)
            if main_details is None:
                message = f"No main info section found for {main_url}"
                print(message)
                return
            product_details = pydash.get(main_details.css("div.large--five-twelfths"), 0)
            images = []
            if product_details is not None and product_details.css("img.lazypreload"):
                product_img = product_details.css("img.lazypreload")
                img_src = product_img.css("img::attr(src)").extract()
                img_alt = product_img.css("img::attr(alt)").extract()
                img_title = product_img.css("img::attr(title)").extract()
                images.append({
                    "src": self.listToString(img_src),
                    "alt": self.listToString(img_alt),
                    "title": self.listToString(img_title),
                })
            name_price_manf_detaisl = pydash.get(main_details.css(
                "div.grid-item.large--seven-twelfths"), 0)
            if name_price_manf_detaisl is None or name_price_manf_detaisl.css("h1[itemprop=name]") is None:
                message = f"No div with class grid-item.large--seven-twelfths found for {main_url}"
                print(message)
                return
            their_name = name_price_manf_detaisl.css(
                "h1[itemprop=name]::text").get()
            if their_name is None:
                message = f"No their_name info found for {main_url}"
                print(message)
                return
            manf_names =""
            if name_price_manf_detaisl.css(
                "p[itemprop=brand].product-meta"):
                manf_names = name_price_manf_detaisl.css(
                    "p[itemprop=brand].product-meta::text").get()
            
            price_info = None
            offers_details = pydash.get(name_price_manf_detaisl.css(
                "div[itemprop = offers]"), 0)
            if offers_details is not None or offers_details.css("ul.inline-list.product-meta") is not None:
                price_details = offers_details.css("ul.inline-list.product-meta")
                if price_details and price_details.css("span.visually-hidden"):
                    price_info = price_details.css(
                        "span.visually-hidden::text").get()
                    if '$' in price_info or ',' in price_info:
                        price_info = price_info.replace('$', '').replace(',', '')

            offers = []
            if price_info is not None:
                offers.append({
                    "condition": "newInBox",
                    "price": {"currency": "USD", "amount": float(price_info)},
                    "stock": None,
                    "instock": True,
                })
            else:
                offers.append({
                    "condition": "newInBox",
                    "price": {"currency": "USD", "amount": price_info},
                    "stock": None,
                    "instock": False,
                })
            today = date.today()
            now = datetime.now()
            d2 = today.strftime("%B %d, %Y")
            current_time = now.strftime("%H:%M:%S")
            date_time = f"{d2} {current_time}"
            description = ""
            long_description = ""

            description_details = pydash.get(main_details.css("div.product-description.rte"), 0)
            if description_details is not None and description_details.css("h3"):
                description = description_details.css("h3::text").get()
                if description_details.css("p.partDesc"):
                    long_description = description_details.css(
                        "p.partDesc::text").extract()
                    long_description = self.listToString(long_description)
            extracted_name = self.extract_unique_name(their_name)
            scrape_object = {
                "url": main_url,
                "alternate_names": "",
                "captured_at": date_time,
                "competitor": self.name,
                "cutsheet_url": "",
                "description": description,
                "images": images,
                "long_description": long_description,
                "manufacturers": manf_names,
                "offers": offers,
                "their_name": their_name,
                "extracted_names": extracted_name,
            }
            yield scrape_object

        except Exception as e:
            print(e)