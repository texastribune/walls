from time import sleep
import numpy as np

from pandas import DataFrame
from pandas import merge
from salesforce_bulk import SalesforceBulk
from simple_salesforce import Salesforce

from config import SALESFORCE

USER = SALESFORCE['USERNAME']
PASS = SALESFORCE['PASSWORD']
TOKEN = SALESFORCE['TOKEN']
HOST = SALESFORCE['HOST']

sf = Salesforce(username=USER, password=PASS, security_token=TOKEN)
session_id = sf.session_id

bulk = SalesforceBulk(sessionId=sf.session_id, host=HOST)

print "Creating job..."
job = bulk.create_query_job("Opportunity", contentType='CSV')
print "Issuing query..."
batch = bulk.query(job, "select AccountId, Amount, CloseDate from Opportunity")
while not bulk.is_batch_done(job, batch):
    print "waiting for query to complete..."
    sleep(3)
bulk.close_job(job)

#for row in bulk.get_batch_result_iter(job, batch, parse_csv=True):
#    import ipdb; ipdb.set_trace()
#    print (row)   # row is a dict
rows = bulk.get_batch_result_iter(job, batch, parse_csv=True)
all = [x for x in rows]

opps = DataFrame.from_dict(all)

job = bulk.create_query_job("Account", contentType='CSV')
print "Creating job..."

batch = bulk.query(job, "SELECT Id, Text_For_Donor_Wall__c FROM Account")
print "Issuing query..."
while not bulk.is_batch_done(job, batch):
    print "waiting for query to complete..."
    sleep(3)
bulk.close_job(job)

rows = bulk.get_batch_result_iter(job, batch, parse_csv=True)
all = [x for x in rows]

accts = DataFrame.from_dict(all)
print len(opps)
# make 'Amount' be numeric and ditch any that aren't:
opps['Amount'] = opps['Amount'].astype(str).convert_objects(convert_numeric=True)
print len(opps)
merged = merge(left=accts, right=opps, how='right', left_on='Id', right_on='AccountId')
# 2009 only:
w2009 = merged[(merged['CloseDate'] > '2008-12-31') & (merged['CloseDate'] < '2010-01-01')]
print len(w2009)
#w2009['Amount'] = w2009['Amount'].astype(float)
grouped = w2009.groupby('AccountId')
final = grouped.aggregate(np.sum)

import ipdb; ipdb.set_trace()
