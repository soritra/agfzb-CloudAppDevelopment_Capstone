#!/usr/bin/env python3
import os
import requests
import json
from time import time
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
# from cloudant.client import Cloudant
from ibm_cloud_sdk_core.authenticators import BearerTokenAuthenticator, IAMAuthenticator
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_watson.natural_language_understanding_v1 import Features, SentimentOptions
from ibmcloudant.cloudant_v1 import AllDocsQuery, CloudantV1, DesignDocument, DesignDocumentViewsMapReduce
from ibm_cloud_sdk_core.get_authenticator import get_authenticator_from_environment

from .models import CarDealer, ExternalToken

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.dev')
load_dotenv(dotenv_path)


# Natural Language Understanding
IBM_NLU_URL = str(os.getenv('IBM_NLU_URL'))
IBM_NLU_API_KEY = str(os.getenv('IBM_NLU_API_KEY'))
IBM_FUNCTION_URL = str(os.getenv('IBM_FUNCTION_URL'))

authenticator = IAMAuthenticator(IBM_NLU_API_KEY)
natural_language_understanding = NaturalLanguageUnderstandingV1(
    version='2022-04-07',
    authenticator=authenticator
)

natural_language_understanding.set_service_url(IBM_NLU_URL)


# Cloudant
IBM_FUNCTION_APIKEY = str(os.getenv('IBM_FUNCTION_APIKEY'))
IBM_FUNCTION_TOKEN = str(os.getenv('IBM_FUNCTION_TOKEN'))
IBM_FUNCTION_GRANT_TYPE = str(os.getenv('IBM_FUNCTION_GRANT_TYPE'))
IBM_CLOUDANT_APIKEY = str(os.getenv('IBM_CLOUDANT_APIKEY'))
IBM_CLOUDANT_URL = str(os.getenv('IBM_CLOUDANT_URL'))
IBM_CLOUDANT_USR = str(os.getenv('IBM_CLOUDANT_USR'))
IBM_CLOUDANT_PWD = str(os.getenv('IBM_CLOUDANT_PWD'))
IBM_CLOUDANT_URL2 = str(os.getenv('IBM_CLOUDANT_URL2'))
IBM_CLOUDANT_KEY2 = str(os.getenv('IBM_CLOUDANT_KEY2'))
IBM_FUNCTION_URL2 = str(os.getenv('IBM_FUNCTION_URL2'))
cloudant_dealerships_db = "dealerships"
cloudant_reviews_db = "reviews"


# cloudant_btoken_authenticator = BearerTokenAuthenticator(IBM_FUNCTION_TOKEN)
cloudant_iam_authenticator = IAMAuthenticator(IBM_CLOUDANT_APIKEY)
cloudant_service = CloudantV1(authenticator=cloudant_iam_authenticator)
cloudant_service.set_service_url(IBM_CLOUDANT_URL)


# make HTTP requests
def get_request(url, **kwargs):
    # print(kwargs)
    print("GET from {} ".format(url))
    params = dict()
    try:
        # Call post method of requests library with URL and parameters
        # Only post method allows to retrieve data with the current version of IBM cloud function action
        headers = {
            'Content-Type': 'application/json',
            'Authorization': "Bearer {}".format(kwargs['token'])
        }
        if not kwargs is None:
            params["text"] = kwargs["text"] if "text" in kwargs else ""
            params["version"] = kwargs["version"] if "version" in kwargs else ""
            params["features"] = kwargs["features"] if "features" in kwargs else ""
            params["return_analyzed_text"] = kwargs["return_analyzed_text"] if "return_analyzed_text" in kwargs else ""
        dt = {}
        if 'dealer_id' in kwargs:
            dt['dealer_id'] = kwargs['dealer_id']
        if 'st' in kwargs:
            dt['st'] = kwargs['st']        
        dt["url"] = IBM_CLOUDANT_URL2
        dt["key"] = IBM_CLOUDANT_KEY2
        data = json.dumps(dt)
        response = requests.post(url, headers=headers, params=params, data=data)
        status_code = response.status_code
        print("With status {} ".format(status_code))
        # print(response.text)
        return response
    except:
        # If any error occurs
        print("Network exception occurred")
        return None


# make HTTP POST requests
def post_request(url, payload, **kwargs):
    url = format_url(url)
    token = get_token()
    print("POST from {} ".format(url))
    headers = {
        'Content-Type': 'application/json',
        'Authorization': "Bearer {}".format(token)
    }
    # print("pload", payload)
    # print("kw", kwargs)    
    payload["url"] = IBM_CLOUDANT_URL2
    payload["key"] = IBM_CLOUDANT_KEY2
    params = dict()
    if not kwargs is None:
        params["text"] = kwargs["text"] if "text" in kwargs else ""
        params["version"] = kwargs["version"] if "version" in kwargs else ""
        params["features"] = kwargs["features"] if "features" in kwargs else ""
        params["return_analyzed_text"] = kwargs["return_analyzed_text"] if "return_analyzed_text" in kwargs else ""
    return requests.post(url, headers=headers, params=params, json=payload)
    

# refresh token
def refresh_token():
    url = "https://iam.cloud.ibm.com/identity/token"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = { 'grant_type': IBM_FUNCTION_GRANT_TYPE, 'apikey': IBM_FUNCTION_APIKEY }
    res = requests.post(url, headers=headers, data=data).json()
    token = { 'value': str(res['access_token']), 'expiration': res['expiration'] }
    new_token = ExternalToken.objects.update_or_create(
        id=1,
        defaults=token
    );        
    return token['value']


# get or refresh token
def get_token():
    try:
        token = ExternalToken.objects.get(id=1)
        print('expire', token.expiration)
        dt = token.expiration - time()
        return token.value if dt >= 300 else refresh_token()    # refresh token if it is to expire in less than 5 minutes
    except ExternalToken.DoesNotExist:        
        return refresh_token()


# get dealers from a cloud function
def get_dealers_from_cf(url, **kwargs):
    url = format_url(url)
    token = get_token()
    results = []
    # Call get_request with a URL and additional parameters
    data = get_request(url, token=token, **kwargs)
    json_res = json.loads(data.text)
    if json_res and 'data' in json_res["response"]["result"]:
        # Get the row list in JSON as dealers
        dealers = json_res["response"]["result"]['data']
        # For each dealer object
        for dealer in dealers:
            # CarDealer object with values in dealer object
            dealer_obj = CarDealer(address=dealer["address"], city=dealer["city"], full_name=dealer["full_name"],
                                  id=dealer["id"], lat=dealer["lat"], long=dealer["long"],
                                  short_name=dealer["short_name"],
                                  st=dealer["st"], zip=dealer["zip"])
            results.append(dealer_obj)
    return results


# retrieve dealer by id from a cloud function
def get_dealer_by_id_from_cf(url, dealer_id):
    # url = format_url(url)
    # token = get_token()
    res = get_dealers_from_cf(url, dealer_id=dealer_id)
    # Call get_request with a URL and additional parameters
    # res = get_request(url, token=token, dealer_id=dealer_id)
    # json_res = json.loads(res.text)
    # print(json_res)
    # if json_res and 'data' in json_res["response"]["result"]:
    #     items = json_res["response"]["result"]['data']
    #     if len(items) > 0:
    #         data = items[0]
    #         dealer = CarDealer(address=data["address"], city=data["city"], full_name=data["full_name"],
    #                           id=data["id"], lat=data["lat"], long=data["long"],
    #                           short_name=data["short_name"],
    #                           st=data["st"], zip=data["zip"])
    return res[0] if len(res) > 0 else None


# retrieve dealers by state
def get_dealers_by_state(url, st):
    return get_dealers_from_cf(url, st=st)


# get reviews by dealer from a cloud function
def get_dealer_reviews_from_cf(url, dealer_id):
    url = format_url(url)
    token = get_token()
    data = get_request(url, token=token, dealer_id=dealer_id)
    results = []
    json_res = json.loads(data.text)
    if json_res and 'data' in json_res["response"]["result"]:
        results = json_res["response"]["result"]['data']
    return results


# call Watson NLU and analyze text
def analyze_review_sentiments(text):
    req = natural_language_understanding.analyze(
        text=text,
        features=Features(sentiment=SentimentOptions())
    )
    response = req.get_result()  
    # - Get the returned sentiment label such as Positive or Negative
    return response['sentiment']['document'] if 'document' in response['sentiment'] else None


# retrieve next review id
def get_next_review_id(url):
    if url:
        token = get_token()
        data = get_request(url, token=token)
        res = json.loads(data.text)
        return res["total_rows"]+1
    else:
        return 0


# format url
def format_url(url):
    return "{}?blocking=true".format(url)

def format_output(item):
  return { k: v for k, v in item["doc"].items() if not k in ['_id', '_rev', 'short_name'] }

  
