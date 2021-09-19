
"""
Under construction
"""

import os
import tweepy as tw
import pandas as pd
import os
from collections import defaultdict
from pymongo import MongoClient

from dotenv import load_dotenv
load_dotenv("../.env")

mongo_cli_username = os.environ.get('MONGO_CLI_USERNAME')
mongo_cli_password = os.environ.get('MONGO_CLI_PASSWORD')
cluster_name = os.environ.get('CLUSTER_NAME')

client = MongoClient(
    "mongodb+srv://{}:{}@{}.plop5.mongodb.net/myFirstDatabase?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE".format(
        mongo_cli_username, mongo_cli_password, cluster_name
    )
)
db = client[mongo_cli_username]

date_since = "2020-02-17"
query_count = 10

keywords = ["amazon"]

class Tweet:
    def __init__(self, date_since, db, keywords, lang="en", query_count=10):
        consumer_key = os.environ.get('tweet_consumer_key')
        consumer_secret = os.environ.get('tweet_consumer_secret')
        access_token = os.environ.get('tweet_access_token')
        access_token_secret = os.environ.get('tweet_access_token_secret')

        self.keywords = keywords

        auth = tw.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tw.API(auth, wait_on_rate_limit=True)
        self.date_since = date_since
        self.query_count = query_count
        self.lang = lang
        # self.col_names = ["user.name", "full_text", "created_at", "lang"]
        self.keyword_dict = defaultdict(list)
        
    # Collect tweets
    def get_tweets(self, keyword):
        self.search_query = '{} OR {} OR {} -filter:links'.format(
            keyword.lower(), keyword.upper(), keyword.title())

        self.tweets = tw.Cursor(self.api.search,
                                q=self.search_query,
                                tweet_mode='extended',
                                lang=self.lang,
                                since=self.date_since).items(self.query_count)

        json_data = [r._json for r in self.tweets]
        dfebn = pd.json_normalize(json_data)
        dfebn["full_text"] = self.clean_entry(dfebn["full_text"])

        for index, row in dfebn.iterrows():
            self.keyword_dict[keyword].append({
                "username": row["user.name"],
                "lang": self.lang,
                "date": row["created_at"],
                "full_text": row["full_text"]
            })

        #add to mongo
        db.tweets.update_many({"keyword": keyword}, {
            "$set": {"tweets": self.keyword_dict[keyword]}}, upsert=True)


    def clean_entry(self, entry):
        return (
            entry
            .replace("\n", "")  # remove new lines
            .replace("\'", "'")  # fix apostrophe
            .replace("\xa0", "")
        )

    def scrape_all(self, keywords):

        for keyword in keywords:
            self.get_tweets(keyword)

        return self.keyword_dict

    

tweet = Tweet(date_since, db, keywords, "en", query_count)
tweets = tweet.scrape_all(keywords)
print(tweets)
