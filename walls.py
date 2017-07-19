from time import sleep
import json

from pandas import DataFrame
import requests
from salesforce_bulk import SalesforceBulk
from simple_salesforce import Salesforce

from config import SALESFORCE
from convert import (convert_sponsors, convert_donors,
        _invert_and_aggregate, _extract_and_map, _sort_circle,
        _strip_sort_key)
from s3 import push_to_s3

# Events and Digital Pages, excluding Festival, and $0
sponsors_query = """
        SELECT Id, AccountId, Amount, CloseDate, Type, RecordTypeId
        FROM Opportunity
        WHERE RecordTypeId IN (
            '01216000001IhmxAAC',
            '01216000001IhIEAA0'
        )
        AND StageName IN ('Closed Won', 'Invoiced', 'Pledged')
        AND Type != 'Earned Revenue'
        AND Amount != 0
    """

# Donations, Grants, and Membership:
donors_query = """
    SELECT Id, AccountId, Amount, CloseDate
    FROM Opportunity
    WHERE RecordTypeId IN (
        '01216000001IhHpAAK',
        '01216000001IhQIAA0',
        '01216000001IhI9AAK'
    )
    AND StageName IN ('Closed Won', 'Pledged')
"""

circle_query = """
    SELECT Text_For_Donor_Wall__c, Membership_Level_TT__c, Name
    FROM Account
    WHERE Membership_Level_TT__c
    LIKE '%Circle'
    AND Membership_Status__c = 'Current'
    ORDER BY Membership_Level_TT__c

"""


class SalesforceConnection(object):
    """
    Represents a connection to Salesforce.

    Creating an instance will authenticate and allow queries
    to be processed.
    """

    def __init__(self):

        payload = {
                'grant_type': 'password',
                'client_id': SALESFORCE['CLIENT_ID'],
                'client_secret': SALESFORCE['CLIENT_SECRET'],
                'username': SALESFORCE['USERNAME'],
                'password': '{0}{1}'.format(SALESFORCE['PASSWORD'],
                    SALESFORCE['TOKEN']),
                }
        token_path = '/services/oauth2/token'
        url = '{0}://{1}{2}'.format('https', SALESFORCE['HOST'],
                token_path)
        # TODO: some error handling here:
        r = requests.post(url, data=payload)
        response = json.loads(r.text)
        self.instance_url = response['instance_url']
        access_token = response['access_token']

        self.headers = {
                'Authorization': 'Bearer {}'.format(access_token),
                'X-PrettyPrint': '1',
                }

    def query(self, query, path='/services/data/v33.0/query'):
        """
        Run a SOQL query against this Salesforce instance.
        """
        url = '{0}{1}'.format(self.instance_url, path)
        if query is None:
            payload = {}
        else:
            payload = {'q': query}
        # TODO: error handling:
        r = requests.get(url, headers=self.headers, params=payload)
        response = json.loads(r.text)
        # recursively get the rest of the records:
        if response['done'] is False:
            return response['records'] + self.query(query=None,
                    path=response['nextRecordsUrl'])
        return response['records']


def generate_circle_data():
    """
    Create a JSON file based on current circle members that
    identifies the level of circle membership. Save this
    file to S3.
    """

    # circle wall
    sf = SalesforceConnection()
    response = sf.query(circle_query)
    new_dict = _extract_and_map(argument=response,
            key='Text_For_Donor_Wall__c',
            value='Membership_Level_TT__c',
            sort_key='Name')
    intermediate = _invert_and_aggregate(new_dict)
    now_sorted = _sort_circle(intermediate)
    final = _strip_sort_key(now_sorted)
    json_output = json.dumps(final)

    push_to_s3(filename='circle-members.json', contents=json_output)


def sf_data(query):
    """
    Get opportunity data using supplied query.
    Get account data.

    Return both as dataframes.

    """

    USER = SALESFORCE['USERNAME']
    PASS = SALESFORCE['PASSWORD']
    TOKEN = SALESFORCE['TOKEN']
    HOST = SALESFORCE['HOST']

    sf = Salesforce(username=USER, password=PASS, security_token=TOKEN)

    bulk = SalesforceBulk(sessionId=sf.session_id, host=HOST)

    print "Creating Opportunity job..."
    job = bulk.create_query_job("Opportunity", contentType='CSV')
    print "Issuing query..."

    batch = bulk.query(job, query)
    while not bulk.is_batch_done(job, batch):
        print "waiting for query to complete..."
        sleep(3)
    bulk.close_job(job)

    rows = bulk.get_batch_result_iter(job, batch, parse_csv=True)
    all = list(rows)

    opps = DataFrame.from_dict(all)

    job = bulk.create_query_job("Account", contentType='CSV')
    print "Creating Account job..."

    batch = bulk.query(job,
            "SELECT Id, Website, Text_For_Donor_Wall__c FROM Account")
    print "Issuing query..."
    while not bulk.is_batch_done(job, batch):
        print "waiting for query to complete..."
        sleep(3)
    bulk.close_job(job)

    rows = bulk.get_batch_result_iter(job, batch, parse_csv=True)

    accts = DataFrame.from_dict(list(rows))
    accts.rename(columns={'Id': 'AccountId'}, inplace=True)

    return opps, accts

# Circles
print "Fetching Circle data..."
generate_circle_data()

# Sponsors
opps, accts = sf_data(sponsors_query)

print "Transforming and exporting to JSON..."
json_output = convert_sponsors(opportunities=opps, accounts=accts)

print "Saving sponsors to S3..."
push_to_s3(filename='sponsors.json', contents=json_output)

# Donors
opps, accounts = sf_data(donors_query)
print "Transforming and exporting to JSON..."
json_output = convert_donors(opportunities=opps, accounts=accts)

print "Saving donors to S3..."
push_to_s3(filename='donors.json', contents=json_output)
