import os

############
# Salesforce
#
MEMBERSHIP_RECORDTYPEID = '01216000001IhHp'
DONATION_RECORDTYPEID = '01216000001IhI9'
TEXASWEEKLY_RECORDTYPEID = '01216000001IhQNAA0'
SALESFORCE = {
    "USERNAME": os.getenv('SALESFORCE_USERNAME'),
    "PASSWORD": os.getenv('SALESFORCE_PASSWORD'),
    "HOST": os.getenv("SALESFORCE_HOST"),
    "TOKEN": os.getenv("SALESFORCE_TOKEN")
}
