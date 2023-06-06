import os
import requests
import json
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
# from cloudant.client import Cloudant
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_watson.natural_language_understanding_v1 import Features, SentimentOptions
from ibmcloudant.cloudant_v1 import AllDocsQuery, CloudantV1, DesignDocument, DesignDocumentViewsMapReduce
from ibm_cloud_sdk_core.get_authenticator import get_authenticator_from_environment

# import related models here


dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.dev')
load_dotenv(dotenv_path)


# Natural Language Understanding
IBM_NLU_URL = str(os.getenv('IBM_NLU_URL'))
IBM_NLU_API_KEY = str(os.getenv('IBM_NLU_API_KEY'))

authenticator = IAMAuthenticator(IBM_NLU_API_KEY)
natural_language_understanding = NaturalLanguageUnderstandingV1(
    version='2022-04-07',
    authenticator=authenticator
)

natural_language_understanding.set_service_url(IBM_NLU_URL)


# Cloudant
IBM_CLOUDANT_APIKEY = str(os.getenv('IBM_CLOUDANT_APIKEY'))
IBM_CLOUDANT_URL = str(os.getenv('IBM_CLOUDANT_URL'))
IBM_CLOUDANT_USR = str(os.getenv('IBM_CLOUDANT_USR'))
IBM_CLOUDANT_PWD = str(os.getenv('IBM_CLOUDANT_PWD'))
cloudant_dealerships_db = "dealerships"
cloudant_reviews_db = "reviews"


cloudant_authenticator = IAMAuthenticator(IBM_CLOUDANT_APIKEY)
cloudant_service = CloudantV1(authenticator=cloudant_authenticator)
cloudant_service.set_service_url(IBM_CLOUDANT_URL)


# make HTTP GET requests
def get_request(params):
  try:
    if (params['type'] == 'nlu'):
      return natural_language_understanding.analyze(
        text=params['text'],
        features=Features(sentiment=SentimentOptions())
      )
    else:
      return cloudant_service.post_search(
        db=params['db'],
        ddoc=params['ddoc'] if 'ddoc' in params else 'search_dealers',
        index=params['index'] if 'index' in params else 'getById',
        query=params['query'] if 'query' in params else "*:*",
        include_docs=True,
        limit=params['limit'] if 'limit' in params else 50
      )
  except:
    return None

# make HTTP POST requests
def post_request(url, params, payload):
  return requests.post(url, params=kwargs, json=payload)


def format_output(item):
  return { k: v for k, v in item["doc"].items() if not k in ['_id', '_rev', 'short_name'] }
  

# get dealers from a cloud function
def get_dealers_from_cf(**kwargs):  
  sort_key = 'full_name'
  req = get_request({
    'type': 'cloudant',
    'db': cloudant_dealerships_db,
    'ddoc': 'search_dealers',
    'index': 'getById',
    'limit': 50
  })
  # print(req)
  if req:
    req.sort_key = sort_key
    response = req.get_result()
    
    dealers = list(map(format_output, response["rows"]))
    print(dealers)
    return sorted(dealers, key=lambda x: x[sort_key])
  else:
    return None


# get reviews by dealer id from a cloud function
def get_dealer_by_id_from_cf(dealerId):
  # - Call get_request() with specified arguments
  req = get_request({
    'type': 'cloudant',
    'db': cloudant_dealerships_db,
    'ddoc': 'search_dealers',
    'index': 'getById',
    'query': 'id:{}'.format(dealerId),
    'limit': 1
  })
  if req:
    response = req.get_result()  
    # print(dealerId, response, 'rows' in response)
    
    # - Parse JSON results into a DealerView object list
    return format_output(response['rows'][0]) if len(response['rows']) > 0 else None
  else:
    return None
  

# retrieve review by dealer from cloud function
def get_review_by_dealer_from_cf(dealerId):
  req = get_request({
    'type': 'cloudant',
    'db': cloudant_reviews_db,
    'ddoc': 'search_reviews',
    'index': 'getByDealer',
    'query': 'dealership:{}'.format(dealerId),
    'limit': None
  })
  if req:
    response = req.get_result()  
    # print(dealerId, response['rows'])
    
    # - Parse JSON results into a DealerView object list
    return list(map(format_output, response["rows"])) if len(response['rows']) > 0 else None
  else:
    return None


# call Watson NLU and analyze text
def analyze_review_sentiments(text):
  # - Call get_request() with specified arguments
  req = get_request({
    'type': 'nlu',
    'text': text
  })
  if req:
    response = req.get_result()  
    # - Get the returned sentiment label such as Positive or Negative
    return response['sentiment']['document'] if 'document' in response['sentiment'] else None
  else:
    return None

