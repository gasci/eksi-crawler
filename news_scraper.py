# -*- coding: utf-8 -*-
"""
Created on Tue Oct 2019
Updated on Mon Apr 2021 

@author: Dr. Göktuğ Aşcı, asuer
"""
#%%
from pymongo import MongoClient
from classes.news import News

import os
# from classes.mesh_keywords import Mesh
from dotenv import load_dotenv
load_dotenv(".env")

mongo_cli_username = os.environ.get('MONGO_CLI_USERNAME')
mongo_cli_password = os.environ.get('MONGO_CLI_PASSWORD')
cluster_name = os.environ.get('CLUSTER_NAME')


#%%

input_location = "data/input/diseases-english.txt"
news_country = input("Select a country (Options: turkey, usa, uk): \n").lower()
news_location = "data/input/news-{}.txt".format(news_country)
url_output_location = r"data/input/mlinks.txt"
countries_list = ["turkey", "usa", "uk"]

# finds news from given countries
if news_country not in countries_list:
    raise ValueError("Options are: turkey, usa, uk")


#%%
# connect to mongo client with a username and password

client = MongoClient(
    "mongodb+srv://{}:{}@{}.plop5.mongodb.net/myFirstDatabase?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE".format(
        mongo_cli_username, mongo_cli_password, cluster_name
    )
)
db = client[mongo_cli_username]
#%%
sources = []

with open(news_location) as my_file:
    for line in my_file:
        sources.append(line.replace("\n", ""))

print("Sources: {}".format(sources))

# Bing new scraper
news = News(sources, db, input_location, news_country)

# scrape all sources
news.scrape_all(url_output_location)
