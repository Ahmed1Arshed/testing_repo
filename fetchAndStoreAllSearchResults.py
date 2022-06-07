import traceback
from utils.service.database.mssql import *
import datetime
import scrapy
import random
import requests
import datetime
import uuid
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
import pydash
from bs4 import BeautifulSoup
import pypyodbc as pyodbc
# client = pymongo.MongoClient(os.getenv('DB'))
# mydb = client["pricing"]

connection_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={user};PWD={password};MultipleActiveResultSets=True "
conn = pyodbc.connect(connection_str)
cursor = conn.cursor()

def listToString(url):
    url_formed = ""
    for f in url:
        url_formed += f
    return url_formed
def setting_proxy(start_urls):
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



def reraise(e, *args):
    '''re-raise an exception with extra arguments
    :param e: The exception to reraise
    :param args: Extra args to add to the exception
    '''

    # e.args is a tuple of arguments that the exception with instantiated with.
    #
    e.args = args + e.args

    # Recreate the expection and preserve the traceback info so that we can see
    # where this exception originated.
    #
    raise e.with_traceback(e.__traceback__)
   
   
def url_insert(data):
    try:
        print("get inside url_insert")
        query = ""
        try:
            if type(data) is not list or len(data) == 0:
                return
            created_by = '652d05be-754c-45ae-99a8-6604126cfaea'
            date = datetime.datetime.combine(
                datetime.date.today() + relativedelta(),
                datetime.time(00, 00, 00))
            chunk_size = 3000
            for i in range(0, len(data), chunk_size):
                data_chunk = data[i:i+chunk_size]
                rows = ""
                for item in data_chunk:
                    name = item.get('competitor')
                    url = item.get('url')
                    scraper_type = item.get('scraper_type')
                    rows += ((", " if len(rows) > 0 else "") +
                            f"(NEWID(), '{name}', '{url}', '{scraper_type}', '{created_by}', '{date}', '{date}')")
                query = f"MERGE INTO scraper_competitor_urls WITH (HOLDLOCK) AS target USING (SELECT * FROM (VALUES {rows}) AS s (id, name, url, scraper_type, created_by, updated_at, created_at)) AS source\
                    ON (target.name=source.name AND target.url=source.url AND target.scraper_type=source.scraper_type)\
                    WHEN NOT MATCHED THEN INSERT (id, name, url, scraper_type, created_by, updated_at, created_at) VALUES (source.id, source.name, source.url, source.scraper_type, source.created_by, source.updated_at, source.created_at);"
                cursor.execute(query)
                conn.commit()
        except Exception as e:
            reraise(e, query)   
    except Exception as e:
        message = "Error: " + str(e) + "\n" + traceback.format_exc()
        print(message)

def iesupply_url():
    outputs = []
    software_names = [SoftwareName.CHROME.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
    user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)
    user_agent = user_agent_rotator.get_random_user_agent()
    headers = {'User-Agent': user_agent, 'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-US,en;q=0.9'}
    url = 'http://www.iesupply.com/sitemaps/sitemap-products-0.xml'
    get_url = setting_proxy(url)
    get_url = get_url.url
    page = requests.get(get_url , headers=headers)
    sitemap_index = BeautifulSoup(page.content, 'html.parser')
    sitemap_url = [element.text for element in sitemap_index.findAll('loc')]
    for data in sitemap_url:
        if 'product' in data:
            result = {
                "competitor":"iesupply",
                "url":data,
                "scraper_type":"sitemap"
            }
            outputs.append(result)
            if len(outputs) == 5000:
                url_insert(outputs)
                outputs = []
    url_insert(outputs)
iesupply_url()