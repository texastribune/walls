from time import sleep
import StringIO
import gzip

from pandas import DataFrame
from salesforce_bulk import SalesforceBulk
from simple_salesforce import Salesforce

from config import SALESFORCE
from convert import convert_sponsors, convert_donors
from s3 import push_to_s3

# Events and Digital Pages
sponsors_query = """
        SELECT Id, AccountId, Amount, CloseDate, Type, RecordTypeId
        FROM Opportunity
        WHERE RecordTypeId IN (
            '01216000001IhmxAAC',
            '01216000001IhIEAA0'
        )
        AND StageName = 'Closed Won'
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
    AND StageName = 'Closed Won'
"""


def sf_data(query):

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

# Sponsors
opps, accts = sf_data(sponsors_query)

print "Transforming and exporting to JSON..."
json_output = convert_sponsors(opportunities=opps, accounts=accts)

out = StringIO.StringIO()
with gzip.GzipFile(fileobj=out, mode="w") as f:
    f.write(json_output)

print "Saving sponsors to S3..."
push_to_s3(filename='sponsors.json.gz', contents=out.getvalue())

# Donors
opps, accounts = sf_data(donors_query)
print "Transforming and exporting to JSON..."
json_output = convert_donors(opportunities=opps, accounts=accts)

out = StringIO.StringIO()
with gzip.GzipFile(fileobj=out, mode="w") as f:
    f.write(json_output)
print "Saving donors to S3..."
push_to_s3(filename='donors.json.gz', contents=out.getvalue())
