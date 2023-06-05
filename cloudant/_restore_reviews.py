#!/usr/bin/env python
import os
import json
from dotenv import load_dotenv

# Connect to service instance by running import statements.
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey

dotenv_path = os.path.join(os.path.dirname(__file__), '.env.dev')
load_dotenv(dotenv_path)


IBM_CLOUDANT_URL = str(os.getenv('IBM_CLOUDANT_URL'))
IBM_CLOUDANT_USR = str(os.getenv('IBM_CLOUDANT_USR'))
IBM_CLOUDANT_PWD = str(os.getenv('IBM_CLOUDANT_PWD'))
db_name = "reviews"


def main():    
    try:
        # Establish a connection with the service instance.
        client = Cloudant(IBM_CLOUDANT_USR, IBM_CLOUDANT_PWD, url=IBM_CLOUDANT_URL)
        client.connect()
    
        # Create database and verify it was created.
        reviews_db = client.create_database(db_name)
        if reviews_db.exists():
            print("Database '{0}' successfully created.\n".format(db_name))
        
        with open('data/reviews-full.json') as file:
            data = json.load(file)
            # print(data['dealerships'])
            for item in data['reviews']:
                newDocument = reviews_db.create_document(item)
                
                # Check that the documents exist in the database.
                if newDocument.exists():
                    print("Document '{0}' successfully created.".format(newDocument['id']))
    except:
        pass


if __name__=='__main__':
    main()

