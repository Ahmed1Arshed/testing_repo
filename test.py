import re
import requests
from bs4 import BeautifulSoup
from utils.helper import *
import pymongo
from pymongo import MongoClient, InsertOne
import os

def controlparts_url():
    outputs = []
    url = 'https://controlparts.com/sitemap_products_1.xml?from=4497408295009&to=4763190591585'
    page = requests.get(url)
    sitemap_index = BeautifulSoup(page.content, 'html.parser')
    sitemap_url = [element.text for element in sitemap_index.findAll('loc')]
    for data in sitemap_url:
        result = {
            "competitor": "controlparts",
            "url": data,
            "scraper_type": "sitemap"
        }
        outputs.append(result)
    print(outputs)