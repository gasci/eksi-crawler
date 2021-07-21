import time
import json
from collections import defaultdict

from selenium import webdriver
from bs4 import BeautifulSoup
from pymongo import MongoClient
import os
import environ

# create an environment file
env = environ.Env()
env.read_env(env.str('ENV_PATH', '.env'))

# disease names are written in this file
input_location = "data/input/diseases-english.txt"

# mongo cluster username and password
mongo_cli_username = os.environ.get('MONGO_CLI_USERNAME')
mongo_cli_password = os.environ.get('MONGO_CLI_PASSWORD')

# connect to mongo cluster
client = MongoClient("mongodb+srv://{}:{}@cluster0.plop5.mongodb.net/myFirstDatabase?retryWrites=true&w=majority".format(
    mongo_cli_username, mongo_cli_password))
db = client['healdash']


class Answer:
    def __init__(self, input_location, db):
        self.keyword_dict = defaultdict(list)
        self.link_list = []
        self.url = ""
        self.input_location = input_location
        self.keywords = []
        self.db = db
        
        # init the browser
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--incognito')
        options.add_argument('--headless')

        driver = webdriver.Chrome()  #  initialize the driver
        self.driver = driver

    def existing_keyword_filter(self):

        existing_news_keywords = []
        
        for document in self.db["wiki_answers"].find():
                existing_news_keywords.append(document['keyword'])

        with open(self.input_location) as my_file:
            for line in my_file:
                self.keywords.append(line.replace("\n", ""))

        # keywords list creation
        self.keywords = [
            item for item in self.keywords if item not in existing_news_keywords]

    def create_url(self, keyword):
        self.url = "https://www.answers.com/search?q={}".format(keyword)

    def scrape_url(self, keyword):

        self.driver.get(self.url)
        self.page_source = BeautifulSoup(self.driver.page_source.encode(
            'utf-8', 'ignore'), features="lxml")  # update page source
        main_divs = self.page_source.find_all('div', {'class': 'grid grid-cols-1 cursor-pointer justify-start items-start'})
       
        all_questions = []

        for main_div in main_divs:
            all_questions.append(main_div.find(
                'div', {'class': 'flex text-primaryColor text-base child-right-margin-4 mb-4 flex-wrap'}, recursive=False))
         
        for question in all_questions:
            try:
                self.scrape_question(question.text[2:], keyword)
            except:
                pass

    def clean_entry(self, entry):
        """
        Fixes formatting issues
        """
        return (
            entry
            .replace("\n", "")  # remove new lines
            .replace("\'", "'")  # fix apostrophe
            .replace("\xa0", "")
            .strip()  # remove spaces
        )

    def scrape_question(self, question, keyword):
        question_underscored = "_".join(question.split(" "))
        question_url = "https://www.answers.com/Q/{}".format(
            question_underscored)
        self.driver.get(question_url)

        question_page_source = BeautifulSoup(self.driver.page_source.encode(
            'utf-8', 'ignore'), features="lxml")  # update page source

     
        self.keyword_dict[keyword].append({
            "question": question[:-2],
            "answer": self.clean_entry(question_page_source.find(
                'div', {'class': 'markdownStyles undefined'}).text)
        })

    def scrape_all(self):

        self.existing_keyword_filter()
        
        for keyword in self.keywords:
            self.create_url(keyword)
            self.scrape_url(keyword)

            # add data to mongodb
            db.wiki_answers.update_many({"keyword": keyword}, {
                                       "$set": {"objects": self.keyword_dict[keyword]}}, upsert=True)
            


answer = Answer(input_location, db)
answer.scrape_all()
