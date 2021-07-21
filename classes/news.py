from newsplease import NewsPlease
from classes.bing_search import Bing
from collections import defaultdict


class News:
    def __init__(self, sources, db, input_location, country="usa"):
        self.sources = sources
        self.article_dict = defaultdict(list)
        self.keywords = []
        self.input_location = input_location
        self.exception = False
        self.documents = []
        self.country = country
        self.db = db

    def get_keywords(self, source):
        """
        Gets desired keywords in the mongodb database
        """

        existing_news_keywords = []
        temp_array = []
        
        for document in self.db["bing_keywords"].find({"source": source}):
            for keyword in document['keywords']:
                existing_news_keywords.append(keyword)


        with open(self.input_location) as my_file:
            for line in my_file:
                temp_array.append(line.replace("\n", ""))

        # keywords list creation
        self.keywords = [
            item for item in temp_array if item not in existing_news_keywords]

        print("{} keywords left for the source: {}".format(
            len(self.keywords), source)
        )

    def upload_articles(self, keyword, source):
        """
        Uploads articles to mongodb database
        """
        for url in self.documents:
            
            try:
                self.exception = False
                article = NewsPlease.from_url(url)
                self.article_dict[keyword].append({
                    "title": article.title,
                    "text": article.maintext,
                    "date": article.date_publish,
                    "language": article.language,
                    "country": self.country
                })
            except:
                self.exception = True
                print("An exception occurred")

            # add data to mongodb
            if not self.exception:
                self.db.bing_news.update_many({"keyword": keyword, "source": source}, {
                    "$set": {"news": self.article_dict[keyword]}}, upsert=True)

        self.db.bing_keywords.update({"source": source}, {
                                     "$addToSet": {"keywords": keyword}}, upsert=True)


    def scrape_all(self, url_output_location):
        """
        Finds relevant articles on Bing using the keywords in the database
        """
        for source in self.sources:

            self.get_keywords(source)

            for keyword in self.keywords:

                url_output_file = open(
                    url_output_location, "w", encoding="utf-8")

                #create a bing object
                bing = Bing(keyword, source, url_output_file)

                #start crawling urls
                bing.crawl_all()

                # writing occurs after this command
                url_output_file.close()

                with open(url_output_location, 'r') as f:
                    y = f.readlines()

                self.documents = [doc.strip('\n') for doc in y]

                print("{} documents found \n".format(len(self.documents)))

                # upload articles to mongodb
                self.upload_articles(keyword, source)

