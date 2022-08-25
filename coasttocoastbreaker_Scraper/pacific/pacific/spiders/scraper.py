import scrapy
import requests
import random
from rq import Queue
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
import re
import pydash
from scrapy_redis.spiders import RedisCrawlSpider

class QuotesSpider(scrapy.Spider):
    name = "quotes"
    custom_settings = {
        'USER_AGENT': 'compitator_scraper (+http://www.yourdomain.com)',
        'DOWNLOADER_MIDDLEWARES' : {
        'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
        'scrapy_rotated_proxy.downloadmiddlewares.proxy.RotatedProxyMiddleware': 750,
        },
        'PROXY_STORAGE' : 'scrapy_rotated_proxy.extensions.file_storage.FileProxyStorage',
        'ROTATED_PROXY_ENABLED' : True,
        # 'DOWNLOAD_DELAY':6,
        'ROBOTSTXT_OBEY':False,
    }

    start_urls = ["https://www.coasttocoastbreaker.com/bab2030-cutler-hammer-circuit-breaker-1.html"]

    def listToString(self, url):
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
        extracted_name_formed = []
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
                extracted_name_formed.append(self.parseNames(baseName_formed))
            return extracted_name_formed
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
            their_name = ""
            main_info = pydash.get(response.css("div.product-info-main"), 0)
            if main_info is None:
                message = f"No main info section found for {main_url}"
                print(message)
                return
            price = None
            price_info = pydash.get(main_info.css("div.price-box.price-final_price"), 0)
            if price_info is not None and price_info.css("span.price"):
                price = price_info.css("span.price::text").get()
                price = price.split("$")
                price = price[1]
                if ',' in price:
                    price = price.replace(',', '')
                if type(price) is str:
                    price = float(price)
            price_formed = {"currency": "USD", "amount": price}
            quantity = ""
            quantity_details = pydash.get(main_info.css("div.product-info-stock-sku"), 0)
            if quantity_details is not None and quantity_details.css("span.stock-qty::text"):
                quantity = quantity_details.css("span.stock-qty::text").get()

            manufacturers = ""
            Amperage = ""
            Voltage = ""
            Ploes = ""
            dt_list = []
            dd_list = []
            product_attributes = response.css("div.product.attribute.attributes")
            product_attributes_info = ""
            description = ""

            http_url = main_url.split("/")
            http_url = [ele for ele in http_url if ele.strip()]
            name_url = http_url[2].split("-")
            # productTitle = pydash.get(response.css("div.breadcrumbs"),0)
            # if productTitle is None:
            #     message = f"No their_name info found div = $('breadcrumbs').text()for {main_url}"
            #     print(message)
            #     return
            # productTitleul = productTitle.css('ul')
            # if productTitleul is not None:
            productTitle = pydash.get(main_info.css("div.product-add-form"),0)
            if productTitle is None:
                message = f"No their_name info found div = $('breadcrumbs').text()for {main_url}"
                print(message)
                return
            their_name = productTitle.css("form#product_addtocart_form::attr(data-product-sku)").get()
            
            script = response.xpath('//script[@type="text/x-magento-init"]/text()').getall()
            
            print("script",script)
            # productTitle = response.css("title::text").get()
            # if productTitle is None:
            #     message = f"No their_name info found productTitle = $('title').text()for {main_url}"
            #     print(message)
            #     return
            # if ' ' in productTitle:
            #     their_name = productTitle.split(' ')[0].strip()
            # else:
            #     their_name = productTitle
            
            if product_attributes is not None and len(product_attributes.css("dt")) > 0:
                for i in range(0, len(product_attributes.css("dt"))):
                    dt_list.append(
                        product_attributes.css("dt ::text")[i].extract())
                    dd_list.append(
                        product_attributes.css("dd ::text")[i].extract())
                    # product_attributes_info += dt_list[i] + " " + dd_list[i] + ","
                    if dt_list[i] == "Manufacturer:":
                        manufacturers += dd_list[i]
                    if dt_list[i] == "Amperage:":
                        Amperage += dd_list[i]
                    if dt_list[i] == "Voltage:":
                        Voltage += dd_list[i]
                    if dt_list[i] == "Poles:":
                        Ploes += dd_list[i]
                    product_attributes_info += dt_list[i] + " " + dd_list[
                        i] + ","
                description_formed = ""

                for x in range(len(name_url)):
                    description_formed += name_url[x] + " "
                description_formed = description_formed.split(".")[0]
                if Amperage == "":
                    description = ""
                    description = description_formed + " -New|" + Voltage + "V|" + Ploes + " ploes"
                    if Voltage == "":
                        description = ""
                        description = description_formed + " -New|" + Ploes + " ploes"
                        if Ploes == "":
                            description = ""
                            description = description_formed
                if Voltage == "":
                    description = ""
                    description = description_formed + " -New|" + Amperage + "A|" + Ploes + " ploes"
                    if Amperage == "":
                        description = ""
                        description = description_formed + " -New|" + Ploes + " ploes"
                        if Ploes == "":
                            description = ""
                            description = description_formed
                if Ploes == "":
                    description = ""
                    description = description_formed + " -New|" + Amperage + "A|" + Voltage + "V|"
                    if Amperage == "":
                        description = ""
                        description = description_formed + " -New|" + Voltage + "V|"
                        if Voltage == "":
                            description = ""
                            description = description_formed
                if Amperage != "" and Voltage != "" and Ploes != "":
                    description = ""
                    description = description_formed + " -New|" + Voltage + \
                        "V|" + Ploes + " ploes|" + "-" + Amperage + "A"
                else:
                    description = ""
                    description = description_formed
            else:
                description = product_attributes_info

            long_description = ""
            if response.css("div.product.attribute.description"):
                product_details_info = response.css("div.product.attribute.description")
                if product_details_info and product_details_info.css("div.value"):
                    product_description = product_details_info.css("div.value::text").getall()
                    for i in range(0, len(product_description)):
                        long_description += product_description[i] + " "

            cutsheet_url = ""
            if main_info.css("div.product.attribute.datasheet"):
                url_info = main_info.css("div.product.attribute.datasheet")
                if url_info and url_info.css("a::attr(href)"):
                    cutsheet_url += str(url_info.css("a::attr(href)").extract())
            offers = []
            condition = "newInBox"
            if '-green' in their_name or '-GREEN' in their_name or '-Green' in their_name:
               condition = "refurbished" 
            if quantity != "":
                offers.append({
                    "condition": condition,
                    "Includes_shipping": "false",
                    "instock": True,
                    "stock": quantity,
                    "price": price_formed,
                })
            else:
                offers.append({
                    "condition": condition,
                    "Includes_shipping": "false",
                    "instock": False,
                    "stock": quantity,
                    "price": price_formed,
                })
            images = []
            if response.css("img.gallery-placeholder__image"):
                img_src = response.css(
                    "img.gallery-placeholder__image ::attr(src) ").extract()
                img_alt_info = response.css(
                    "img.gallery-placeholder__image ::attr(alt) ").extract()
                img_title_info = response.css(
                    "img.gallery-placeholder__image ::attr(title) ").extract()
                img_alt = ""
                img_title = ""
                for i in range(0, len(img_alt_info)):
                    img_alt += img_alt_info[i]
                for i in range(0, len(img_title_info)):
                    img_title += img_title_info[i]

                images.append({
                    "src": self.listToString(img_src),
                    "alt": img_alt,
                    "title": img_title,
                })
            extracted_name = self.extract_unique_name(their_name)
            scrape_object = {
                "test":their_name
                # "url": main_url,
                # "cutsheet_url": cutsheet_url,
                # "manufacturers": manufacturers,
                # "their_name": their_name,
                # "alternate_names": "",
                # "extracted_names": extracted_name,
                # "competitor": self.name,
                # "description": description,
                # "long_description": long_description,
                # "images": images,
                # "offers": offers,
                # "captured_at": date_time
            }
            print(scrape_object)
            yield scrape_object
        except Exception as e:
            print(e)
