from decimal import Decimal, ROUND_HALF_UP
import json

import pandas as pd

DIGITAL_PAGES = '01216000001IhIEAA0'
EVENT_SPONSORSHIPS = '01216000001IhmxAAC'


def make_pretty_money(amount):
    """
    Round to nearest dollar. Format nicely.
    """
    amount = Decimal(amount)
    amount = amount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    amount = '${:,.0f}'.format(amount)
    return amount


def digital_revenue(row):
    """
    Create digital revenue column.
    """
    if row['Type'] != 'In-Kind' and row[
            'RecordTypeId'] == DIGITAL_PAGES:
        row['digital_revenue'] = row['Amount']
    else:
        row['digital_revenue'] = 0
    return row


def digital_in_kind(row):
    """
    Create in kind digital revenue column.
    """
    if row['Type'] == 'In-Kind' and row[
            'RecordTypeId'] == DIGITAL_PAGES:
        row['digital_in_kind'] = row['Amount']
    else:
        row['digital_in_kind'] = 0
    return row


def events_in_kind(row):
    """
    Create in kind events column.
    """
    if row['Type'] == 'In-Kind' and row[
            'RecordTypeId'] == EVENT_SPONSORSHIPS:
        row['events_in_kind'] = row['Amount']
    else:
        row['events_in_kind'] = 0
    return row


def events_revenue(row):
    """
    Create events column.
    """
    if row['Type'] != 'In-Kind' and row[
            'RecordTypeId'] == EVENT_SPONSORSHIPS:
        row['events_revenue'] = row['Amount']
    else:
        row['events_revenue'] = 0
    return row


def clean_url(string):
    """
    Given a url that doesn't conform to http://something.here
    make it look like that.
    """
    if string == 'NULL':
        return ''
    if string == 'http://':
        return ''
    if string == '':
        return string
    if string.startswith('http'):
        return string
    return "http://" + string


def convert_sponsors(accounts, opportunities):
    """
    Takes two pandas dataframes: one mapping account IDs to names and URLs
    and another with the opportunities.

    It returns a JSON string suitable for use in a web app.

    """

    # make a dict mapping Account ID to Sponsor Wall text:
    wall_text_dict = accounts.set_index(
            'AccountId')['Text_For_Donor_Wall__c'].to_dict()
    # and another mapping to URL:
    url_dict = accounts.set_index(
            'AccountId')['Website'].to_dict()

    # make 'Amount' be numeric:
    opportunities['Amount'] = pd.to_numeric(opportunities['Amount'],
            errors='coerce')
    opportunities = opportunities.dropna()

    # drop opps that have no account
    opportunities = opportunities[opportunities.AccountId != '']

    # convert to an actual date:
    opportunities['CloseDate'] = pd.to_datetime(opportunities['CloseDate'])

    # we only need the year and this will let us pivot by it:
    opportunities['Year'] = [x.year for x in opportunities.CloseDate]

    # these split the different revenue types into different columns
    # there's probably better/other ways to do this but I don't know
    # them (yet)
    opportunities = opportunities.apply(digital_revenue, axis=1)
    opportunities = opportunities.apply(digital_in_kind, axis=1)
    opportunities = opportunities.apply(events_revenue, axis=1)
    opportunities = opportunities.apply(events_in_kind, axis=1)

    # we no longer need this column now:
    del opportunities['Amount']

    # calculate all-time numbers and set that as a 'year'
    all_time = opportunities.pivot_table(index=['AccountId'], aggfunc=sum)
    all_time.Year = 'all-time'
    all_time = all_time.reset_index()

    both = pd.concat([opportunities, all_time])
    final = both.pivot_table(index=['Year', 'AccountId'], aggfunc=sum)
    final['total'] = final.sum(axis=1)

    # convert to a dict that will map to JSON
    final_dict = {}
    for year, new_df in final.groupby(level=0):
        year_list = []
        for row in new_df.iterrows():
            accountid = row[0][1]
            account_dict = {
                'sponsor': wall_text_dict[accountid],
                'url': clean_url(url_dict[accountid]),
                'digital_revenue': make_pretty_money(
                    row[1]['digital_revenue']),
                'digital_in_kind': make_pretty_money(
                    row[1]['digital_in_kind']),
                'events_revenue': make_pretty_money(row[1]['events_revenue']),
                'events_in_kind': make_pretty_money(row[1]['events_in_kind']),
                'total': make_pretty_money(row[1]['total']),
                }
            year_list.append(account_dict)
        final_dict[year] = sorted(year_list, key=lambda k: k['sponsor'])

    export = json.dumps(final_dict, indent=4)
    return export


def convert_donors(accounts, opportunities):
    """
    Takes two pandas dataframes: one mapping account IDs to names and
    another with the opportunities.

    It returns a JSON string suitable for use in a web app.

    The dataframes should look like this:

    opportunities = DataFrame({
        "AccountId": ["A01", "B01", "A01", "B01"],
        "Amount": [1, 2, 3, 4],
        "CloseDate": ['2009-01-02', '2009-01-03', '2009-01-04', '2010-01-02']
    })

    accounts = DataFrame({
        "AccountId": ["A01", "B01"],
        "Text_For_Donor_Wall__c": ["Donor A", "Donor B"]
    })

    """

    # make a dict mapping Account ID to Donor Wall text:
    accounts_dict = accounts.set_index(
            'AccountId')['Text_For_Donor_Wall__c'].to_dict()

    # make 'Amount' be numeric:
    opportunities['Amount'] = pd.to_numeric(opportunities['Amount'],
            errors='coerce')
    opportunities = opportunities.dropna()

    # drop opps that have no account
    opportunities = opportunities[opportunities.AccountId != '']

    # convert to an actual date:
    opportunities['CloseDate'] = pd.to_datetime(opportunities['CloseDate'])
    # we only need the year and this will let us pivot by it:
    opportunities['Year'] = [x.year for x in opportunities.CloseDate]

    all_time = opportunities.pivot_table(index=['AccountId'], aggfunc=sum)
    all_time.Year = 'all-time'
    all_time = all_time.reset_index()
    both = pd.concat([opportunities, all_time])
    final = both.pivot_table(index=['AccountId', 'Year'], aggfunc=sum)

    final_list = list()

    # convert to a dict that will map to JSON
    for accountid, new_df in final.groupby(level=0):
        account_dict = {
                'name': accounts_dict[accountid]
                }
        account_dict['donations'] = list()
        for row in new_df.iterrows():
            year = row[0][1]
            amount = row[1][0]
            amount = Decimal(amount)
            amount = amount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            if amount < 10:
                amount = "Less than $10"
            else:
                amount = '${:,.0f}'.format(amount)

            donations_dict = {
                    'year': year,
                    'amount': '{}'.format(amount)
                    }
            account_dict['donations'].append(donations_dict)
        final_list.append(account_dict)

    export = json.dumps(final_list, indent=4)
    return export


def _extract_and_map(argument=None, key=None, value=None):
    """
    Transform a list with dictionaries like this:
    key1: value1
    key2: value2

    To a dictionary like this:

    value1: value2

    See tests.py for an example.
    """
    _ = dict()
    for item in argument:
        _[item[key]] = item[value]
    return _


def _invert_and_aggregate(the_dict):
    """
    Transform a dictionary like this:

    { key1: value1,
      key2: value2,
      key3: value2 }

    Into a dictionary of lists like this:

    { value1: [ key1 ],
      value2: [ key2, key3 ] }

    See tests.py for an example:
    """
    _ = {}
    # invert it
    for k, v in the_dict.items():
        _.setdefault(v, []).append(k)
    return _


if __name__ == "__main__":

    # These are examples for testing:

    from pandas import DataFrame
    opportunities = DataFrame({
        "AccountId": ["A01", "B01", "A01", "B01"],
        "Amount": [5, 20, 4, 4000],
        "CloseDate": ['2009-01-02', '2009-01-03', '2009-01-04', '2010-01-02']
    })

    accounts = DataFrame({
        "AccountId": ["A01", "B01"],
        "Text_For_Donor_Wall__c": ["Donor A", "Donor B"]
    })
    foo = convert_donors(opportunities=opportunities, accounts=accounts)
    print foo

    opportunities = DataFrame({
        "AccountId": ["A01", "B01", "A01", "B01", "B01"],
        "Amount": [5, 20, 4, 40, 30],
        "CloseDate": ['2009-01-02', '2009-01-03', '2009-01-04',
            '2010-01-02', '2010-01-02'],
        "RecordTypeId": ['01216000001IhIEAA0', '01216000001IhIEAA0',
            '01216000001IhmxAAC', '01216000001IhmxAAC', '01216000001IhmxAAC'],
        "Type": ['Standard', 'In-Kind', '', 'In-Kind', ''],
    })

    accounts = DataFrame({
        "AccountId": ["A01", "B01"],
        "Text_For_Donor_Wall__c": ["Donor A", "Donor B"],
        "Website": ['http://A01.com', 'http://B01.com'],
    })
    foo = convert_sponsors(opportunities=opportunities, accounts=accounts)
    print foo
