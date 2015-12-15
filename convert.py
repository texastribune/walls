import json

import pandas as pd

# TODO: exclude certain types of revenue

def export_to_json(accounts, opportunities):
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
    opportunities.Amount = opportunities['Amount'].astype(float)

    # convert to an actual date:
    opportunities['CloseDate'] = pd.to_datetime(opportunities['CloseDate'])

    # we only need the year and this will let us pivot by it:
    opportunities['Year'] = [x.year for x in opportunities.CloseDate]

    final = opportunities.pivot_table(index=['AccountId', 'Year'], aggfunc=sum)

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
            donations_dict = {
                    'year': year,
                    'amount': amount
                    }
            account_dict['donations'].append(donations_dict)
        final_list.append(account_dict)

    export = json.dumps(final_list, indent=4)
    return export

if __name__ == "__main__":
    import doctest
    doctest.testmod()


