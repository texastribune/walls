import os

# This value should be set to the frequency that this job is run. Right now I
# believe it will be called every 12 hours. If that changes this should too:
HOURS_TO_EXPIRE = 12

# where to store the compress JSON:
BUCKET = 'membership.texastribune.org'

SALESFORCE = {
    "USERNAME": os.getenv('SALESFORCE_USERNAME'),
    "PASSWORD": os.getenv('SALESFORCE_PASSWORD'),
    "HOST": os.getenv("SALESFORCE_HOST"),
    "TOKEN": os.getenv("SALESFORCE_TOKEN"),
    "CLIENT_ID": os.getenv("SALESFORCE_CLIENT_ID"),
    "CLIENT_SECRET": os.getenv("SALESFORCE_CLIENT_SECRET"),
}
