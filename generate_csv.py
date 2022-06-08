import pymongo
import csv
import os

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["pricing"]

filename = 'products_data.csv'
fieldnames = ['their_name', 'competitor']

def get_data_and_generate_csv():
    if os.path.exists(filename):
        os.remove(filename)
    skip = 0
    chunk = 20000
    products_count = True
    while products_count:
        cursor = db.competitorproducts.find({"isMatch": True}).skip(skip).limit(chunk)
        products = [product for product in cursor]
        with open(filename, 'a', encoding='UTF8', newline='') as f:
            writer = csv.DictWriter(f, extrasaction='ignore', fieldnames=fieldnames)
            writer.writerows(products)
        products_count = len(products)
        skip += chunk

get_data_and_generate_csv()