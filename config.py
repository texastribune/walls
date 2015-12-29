import os

SALESFORCE = {
    "USERNAME": os.getenv('SALESFORCE_USERNAME'),
    "PASSWORD": os.getenv('SALESFORCE_PASSWORD'),
    "HOST": os.getenv("SALESFORCE_HOST"),
    "TOKEN": os.getenv("SALESFORCE_TOKEN")
}
