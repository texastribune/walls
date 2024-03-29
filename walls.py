import json
from time import sleep

import requests
import unicodecsv
from pandas import DataFrame
from salesforce_bulk import SalesforceBulk
from simple_salesforce import Salesforce

from config import SALESFORCE
from convert import (
    _extract_and_map,
    _invert_and_aggregate,
    _sort_circle,
    _strip_sort_key,
    convert_donors,
    convert_sponsors,
)
from s3 import push_to_s3

# Events and Digital Pages, excluding Festival, and $0
sponsors_query = """
        SELECT Id, AccountId, Amount, CloseDate, Type, RecordTypeId
        FROM Opportunity
        WHERE RecordTypeId IN (
            '01216000001IhmxAAC',
            '01216000001IhIEAA0',
            '01246000000hj93AAA',
            '01216000001IhvaAAC'
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
            "grant_type": "password",
            "client_id": SALESFORCE["CLIENT_ID"],
            "client_secret": SALESFORCE["CLIENT_SECRET"],
            "username": SALESFORCE["USERNAME"],
            "password": "{0}{1}".format(SALESFORCE["PASSWORD"], SALESFORCE["TOKEN"]),
        }
        token_path = "/services/oauth2/token"
        url = "{0}://{1}{2}".format("https", SALESFORCE["HOST"], token_path)
        # TODO: some error handling here:
        r = requests.post(url, data=payload)
        response = json.loads(r.text)
        self.instance_url = response["instance_url"]
        access_token = response["access_token"]

        self.headers = {
            "Authorization": "Bearer {}".format(access_token),
            "X-PrettyPrint": "1",
        }

    def query(self, query, path="/services/data/v33.0/query"):
        """
        Run a SOQL query against this Salesforce instance.
        """
        url = "{0}{1}".format(self.instance_url, path)
        if query is None:
            payload = {}
        else:
            payload = {"q": query}
        # TODO: error handling:
        r = requests.get(url, headers=self.headers, params=payload)
        response = json.loads(r.text)
        # recursively get the rest of the records:
        if response["done"] is False:
            return response["records"] + self.query(
                query=None, path=response["nextRecordsUrl"]
            )
        return response["records"]


def business_roster():

    sf = SalesforceConnection()

    path = "/services/data/v43.0/analytics/reports/00O46000000hUA3"
    url = "{}{}".format(sf.instance_url, path)
    resp = requests.get(url, headers=sf.headers)
    content = json.loads(resp.text)
    final = dict()
    for item in content["factMap"]["T!T"]["rows"]:
        tmp = dict()
        tmp["business_name"] = item["dataCells"][0]["label"]
        tmp["url"] = item["dataCells"][1]["value"]
        level = item["dataCells"][2]["label"]
        if level not in final:
            final[level] = list()
        final[level].append(tmp)

    final = json.dumps(final)
    return final


def generate_circle_data():
    """
    Create a JSON file based on current circle members that
    identifies the level of circle membership. Save this
    file to S3.
    """

    # circle wall
    sf = SalesforceConnection()
    response = sf.query(circle_query)
    new_dict = _extract_and_map(
        argument=response,
        key="Text_For_Donor_Wall__c",
        value="Membership_Level_TT__c",
        sort_key="Name",
    )
    intermediate = _invert_and_aggregate(new_dict)
    now_sorted = _sort_circle(intermediate)
    final = _strip_sort_key(now_sorted)
    json_output = json.dumps(final)

    push_to_s3(filename="circle-members.json", contents=json_output)


def sf_data(query):
    """
    Get opportunity data using supplied query.
    Get account data.

    Return both as dataframes.

    """

    USER = SALESFORCE["USERNAME"]
    PASS = SALESFORCE["PASSWORD"]
    TOKEN = SALESFORCE["TOKEN"]
    HOST = SALESFORCE["HOST"]

    sf = Salesforce(username=USER, password=PASS, security_token=TOKEN)

    bulk = SalesforceBulk(sessionId=sf.session_id, host=HOST)

    print("Creating Opportunity job...")
    job = bulk.create_query_job("Opportunity", contentType="CSV")
    print("Issuing query...")

    batch = bulk.query(job, query)
    bulk.close_job(job)
    while not bulk.is_batch_done(batch):
        print("waiting for query to complete...")
        sleep(3)

    rows = list()
    for result in bulk.get_all_results_for_query_batch(batch):
        reader = unicodecsv.DictReader(result, encoding="utf-8")
        for row in reader:
            rows.append(row)

    opps = DataFrame.from_dict(rows)

    job = bulk.create_query_job("Account", contentType="CSV")
    print("Creating Account job...")

    batch = bulk.query(job, "SELECT Id, Website, Text_For_Donor_Wall__c FROM Account")
    print("Issuing query...")
    while not bulk.is_batch_done(batch):
        print("waiting for query to complete...")
        sleep(3)
    bulk.close_job(job)

    rows = list()
    for result in bulk.get_all_results_for_query_batch(batch):
        reader = unicodecsv.DictReader(result, encoding="utf-8")
        for row in reader:
            rows.append(row)

    accts = DataFrame.from_dict(list(rows))
    accts.rename(columns={"Id": "AccountId"}, inplace=True)

    return opps, accts


# Circles
print("Fetching Circle data...")
generate_circle_data()

# Sponsors
print("Fetching Sponsor data...")
opps, accts = sf_data(sponsors_query)

print("Transforming and exporting to JSON...")
json_output = convert_sponsors(opportunities=opps, accounts=accts)

print("Saving sponsors to S3...")
push_to_s3(filename="sponsors.json", contents=json_output)

# Business memberships
print("Fetching business membership data...")
json_output = business_roster()

print("Saving business roster to S3...")
push_to_s3(filename="business-member-roster.json", contents=json_output)

# Donors
opps, accounts = sf_data(donors_query)
print("Transforming and exporting to JSON...")
json_output = convert_donors(opportunities=opps, accounts=accts)

print("Saving donors to S3...")
push_to_s3(filename="donors.json", contents=json_output)
