import pymongo
from pymongo import MongoClient, InsertOne
from threading import Thread
import re
from multiprocessing.pool import ThreadPool
import concurrent.futures
from proxy import *
from datetime import datetime
from elasticsearch import Elasticsearch
client = pymongo.MongoClient("mongodb://localhost:27017/")
es = Elasticsearch(
    "https://7b691ab396694b38b52769880c6f0520.westus2.azure.elastic-cloud.com:9243/",
    basic_auth=("elastic", "uaUZkeHzDzI9SnJee5NH8jRM"))
search_param = {
    "query":{"bool": 
                    {"must":[
                        {"term":{"is_deleted":False}}]
                    }
                },
                "fields": ["name"],
                "_source": False
            }

def listToString(url):
    url_formed = ""
    for f in url:
        url_formed += f
    return url_formed

def extracted_name(skip_limit_start,skip_limit_end):
    result = []
    response = None
    while response is None or response.get('hits').get('hits') is None:
        response = es.search(index="products", body=search_param , from_=skip_limit_start, size=skip_limit_end)
        for data in response.get('hits').get('hits'):
            result.append(listToString(data.get('fields').get('name')))
    return result

url = "https://www.coasttocoastbreaker.com/search/ajax/suggest/?q="
def product_name():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("start of function " , current_time)
    mydb = client["existing_name"]
    mydb_col = mydb["names"]
    mydb_col_output = mydb_col.find()
    # names = get_name()
    executor = concurrent.futures.ThreadPoolExecutor(200)
    # for data in mydb_col_output:
        # executor.submit(creating_url, data.get("name"))
    for data in mydb_col_output:
        executor.submit(creating_url, data.get("name"))
def creating_url(name):
    url_formed = url
    url_formed += name
    request = setting_proxy(url_formed)
    requ = request.url
    req = requests.get(requ)
    url_content = req.content
    url_content = url_content.decode()
    list_url = []
    for u in re.findall('(https:\S+.html)', url_content):
        list_url.append(u)
    if len(list_url) != 0:
        result = {
            "competitor" : "coasttocoastbreaker",
            "url": list_url,
            }
        list_url = []
        # global count
        # count = count + 1
        # print("RESULT",count , name, result)
        print(result)
        # storing_data(result)

def storing_data(result):
    mydb = client["pacific_data"]
    mydb.coasttocoastbreaker_url.insert_one(result)

product_name()
