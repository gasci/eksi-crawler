# -*- coding: utf-8 -*-
"""
Created on Tue Oct 2019
Updated on Mon Apr 2021 

@author: Dr. Göktuğ Aşcı, asuer
"""

import sys
import pandas as pd
from pymongo import MongoClient
from classes.news import News
from classes.mesh_keywords import Mesh
import os
import environ


# read environment variables from .env file
env = environ.Env()
env.read_env(env.str('ENV_PATH', '.env'))

input_location = "data/input/diseases-english.txt"
news_country = input("Select a country (Options: turkey, usa, uk): \n").lower()
news_location = "data/input/news-{}.txt".format(news_country)
url_output_location = r"data/input/mlinks.txt"
countries_list = ["turkey", "usa", "uk"]

# finds news from given countries 
if news_country not in countries_list:
    raise ValueError("Options are: turkey, usa, uk")

# connect to mongo client with a username and password
mongo_cli_username = os.environ.get('MONGO_CLI_USERNAME')
mongo_cli_password = os.environ.get('MONGO_CLI_PASSWORD')

client = MongoClient("mongodb+srv://{}:{}@cluster0.plop5.mongodb.net/myFirstDatabase?retryWrites=true&w=majority".format(mongo_cli_username, mongo_cli_password))
db = client['healdash']

sources = []

with open(news_location) as my_file:
    for line in my_file:
        sources.append(line.replace("\n", ""))

print("Sources: {}".format(sources))

# Bing new scraper 
news = News(sources, db, input_location, news_country)

# scrape all sources
news.scrape_all(url_output_location)
