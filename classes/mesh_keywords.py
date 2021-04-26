# importing the requests library
import requests
from pymongo import MongoClient
from collections import defaultdict
import time


class Mesh:
    def __init__(self, input_location, db):
        self.query_term = ""
        self.query = ""
        self.keyword_dict = defaultdict(list)
        self.keywords_to_update = []
        self.api_url = "https://id.nlm.nih.gov/mesh/sparql"
        self.query_terms = set()
        self.db = db

        with open(input_location) as my_file:
            for line in my_file:
                self.query_terms.add(line.replace("\n", ""))

    def update_query(self, query_term):
        self.query_term = query_term
        self.query = """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#>
            PREFIX mesh: <http://id.nlm.nih.gov/mesh/>

            SELECT ?d ?dName ?c ?cName ?t ?v
            WHERE { 
              ?d a meshv:Descriptor .
              ?d meshv:concept ?c .
              ?d ?t ?c .
              ?t rdfs:label ?v .
              ?d rdfs:label ?dName .
              ?c rdfs:label ?cName
              FILTER(REGEX(?dName,"%s",'i') || REGEX(?cName,"%s",'i')) 
            }
            """ % (query_term, query_term)

    def send_request(self, format="JSON", limit=1000, inference="true", offset=0):

        # defining a params dict for the parameters to be sent to the API
        PARAMS = {'query': self.query, 'format': format,
                  'limit': limit, 'offset': offset, 'inference': inference}

        # sending get request and saving the response as response object
        result = requests.get(url=self.api_url, params=PARAMS)

        # extracting data in json format
        values_dict = result.json()['results']['bindings']

        existing_words = []
        temp_arr = []

        for sub in values_dict:
            temp_dict = defaultdict(list)
            temp_word = sub['cName']['value']

            if temp_word not in existing_words:
                temp_dict['resource'] = sub['c']['value']
                temp_dict['word'] = temp_word
                temp_dict['label'] = sub['dName']['value']
                temp_arr.append(temp_dict)
                existing_words.append(temp_word)

        self.keyword_dict[self.query_term] = temp_arr

    def get_keyword_synonyms(self) -> dict:

        existing_mesh_keywords = set()
        for document in self.db["mesh_synonyms"].find():
            existing_mesh_keywords.add(document['keyword'])  

        # don't use existing mesh synonyms
        self.query_terms = self.query_terms.difference(existing_mesh_keywords)

        for keyword in self.query_terms:
            self.update_query(keyword)
            start_time = time.time()
            self.send_request()

            if len(self.keyword_dict[keyword]) != 0:
                # add data to mongodb
                print("{} - {:.0f} seconds".format(keyword,
                                                   time.time() - start_time))
                self.db.mesh_synonyms.update_many({"keyword": keyword}, {
                                             "$set": {"synonyms": self.keyword_dict[keyword]}}, upsert=True)
            else:
                self.keywords_to_update.append(keyword)
                print("{} - No synonymns".format(keyword))

        return self.keyword_dict
