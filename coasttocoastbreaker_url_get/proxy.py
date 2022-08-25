import random
import scrapy
import requests
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

def listToString(url):
        url_formed = ""
        for f in url: 
            url_formed += f
        return url_formed
         

def setting_proxy(start_urls ):
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
    request = scrapy.Request(url=listToString(start_urls),method='GET', headers= headers)
    request.meta['proxy'] = rand_url
    request.meta['tunnel'] = True
    return request
