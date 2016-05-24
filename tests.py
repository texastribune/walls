import json
from pandas import DataFrame

from convert import (convert_donors, convert_sponsors, clean_url,
        make_pretty_money, _extract_and_map, _invert_and_aggregate,
        _sort_circle, _strip_sort_key)


def test_convert_to_json_with_empty_amount():
    """
    Verify that blank values are ignored.
    """

    opportunities = DataFrame({
        "AccountId": ["A01", "B01", "A01", "B01"],
        "Amount": [10, 20, 30, ''],
        "CloseDate": ['2009-01-02', '2009-01-03', '2009-01-04', '2010-01-02']
    })

    accounts = DataFrame({
        "AccountId": ["A01", "B01"],
        "Text_For_Donor_Wall__c": ["Donor A", "Donor B"]
    })
    actual = convert_donors(opportunities=opportunities, accounts=accounts)
    expected = """
    [
        {
            "donations": [
                {
                    "amount": "$40",
                    "year": 2009
                },
                {
                    "amount": "$40",
                    "year": "all-time"
                }
            ],
            "name": "Donor A"
        },
        {
            "donations": [
                {
                    "amount": "$20",
                    "year": 2009
                },
                {
                    "amount": "$20",
                    "year": "all-time"
                }
            ],
            "name": "Donor B"
        }
    ]
    """
    assert json.loads(actual) == json.loads(expected)


def test_convert_to_json_normal():
    """
    Check the normal case.
    """

    opportunities = DataFrame({
        "AccountId": ["A01", "B01", "A01", "B01"],
        "Amount": [10, 20, 30, 4000],
        "CloseDate": ['2009-01-02', '2009-01-03', '2009-01-04', '2010-01-02']
    })

    accounts = DataFrame({
        "AccountId": ["A01", "B01"],
        "Text_For_Donor_Wall__c": ["Donor A", "Donor B"]
    })
    expected = """
    [
        {
            "donations": [
                {
                    "amount": "$40",
                    "year": 2009
                },
                {
                    "amount": "$40",
                    "year": "all-time"
                }
            ],
            "name": "Donor A"
        },
        {
            "donations": [
                {
                    "amount": "$20",
                    "year": 2009
                },
                {
                    "amount": "$4,000",
                    "year": 2010
                },
                {
                    "amount": "$4,020",
                    "year": "all-time"
                }
            ],
            "name": "Donor B"
        }
    ]
    """

    actual = convert_donors(opportunities=opportunities, accounts=accounts)
    assert json.loads(actual) == json.loads(expected)


def test_convert_to_json_under_10():
    """
    Confirm that totals under $10 are aggregated.
    """

    opportunities = DataFrame({
        "AccountId": ["A01", "B01", "A01", "B01"],
        "Amount": [5, 20, 4, 4000],
        "CloseDate": ['2009-01-02', '2009-01-03', '2009-01-04', '2010-01-02']
    })

    accounts = DataFrame({
        "AccountId": ["A01", "B01"],
        "Text_For_Donor_Wall__c": ["Donor A", "Donor B"]
    })
    expected = """
    [
        {
            "donations": [
                {
                    "amount": "Less than $10",
                    "year": 2009
                },
                {
                    "amount": "Less than $10",
                    "year": "all-time"
                }
            ],
            "name": "Donor A"
        },
        {
            "donations": [
                {
                    "amount": "$20",
                    "year": 2009
                },
                {
                    "amount": "$4,000",
                    "year": 2010
                },
                {
                    "amount": "$4,020",
                    "year": "all-time"
                }
            ],
            "name": "Donor B"
        }
    ]
    """

    actual = convert_donors(opportunities=opportunities, accounts=accounts)
    assert json.loads(actual) == json.loads(expected)


def test_convert_to_json_all_time():
    """
    Check all time.
    """

    opportunities = DataFrame({
        "AccountId": ["A01", "B01", "A01", "B01"],
        "Amount": [5, 20, 4, 4000],
        "CloseDate": ['2009-01-02', '2009-01-03', '2009-01-04', '2010-01-02']
    })

    accounts = DataFrame({
        "AccountId": ["A01", "B01"],
        "Text_For_Donor_Wall__c": ["Donor A", "Donor B"]
    })
    expected = """
    [
        {
            "donations": [
                {
                    "amount": "Less than $10",
                    "year": 2009
                },
                {
                    "amount": "Less than $10",
                    "year": "all-time"
                }
            ],
            "name": "Donor A"
        },
        {
            "donations": [
                {
                    "amount": "$20",
                    "year": 2009
                },
                {
                    "amount": "$4,000",
                    "year": 2010
                },
                {
                    "amount": "$4,020",
                    "year": "all-time"
                }
            ],
            "name": "Donor B"
        }
    ]
    """

    actual = convert_donors(opportunities=opportunities, accounts=accounts)
    assert json.loads(actual) == json.loads(expected)


def test_make_pretty_money_commas():
    """
    Check that commas get inserted in values over $999.
    """

    input = 4000
    expected = '$4,000'
    actual = make_pretty_money(input)
    assert actual == expected


def test_make_pretty_money_rounding():
    """
    Check that rounding works.
    """

    input = 4.50
    expected = '$5'
    actual = make_pretty_money(input)
    assert actual == expected


def test_make_pretty_money_round_down():
    """
    Check that rounding works.
    """

    input = 4.49
    expected = '$4'
    actual = make_pretty_money(input)
    assert actual == expected


def test_sponsors():
    """
    Do an end-to-end sponsor check.
    """

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

    expected = """{
        "2009": [
            {
                "events_revenue": "$4",
                "digital_in_kind": "$0",
                "sponsor": "Donor A",
                "url": "http://A01.com",
                "events_in_kind": "$0",
                "total": "$9",
                "digital_revenue": "$5"
            },
            {
                "events_revenue": "$0",
                "digital_in_kind": "$20",
                "sponsor": "Donor B",
                "url": "http://B01.com",
                "events_in_kind": "$0",
                "total": "$20",
                "digital_revenue": "$0"
            }
        ],
        "2010": [
            {
                "events_revenue": "$30",
                "digital_in_kind": "$0",
                "sponsor": "Donor B",
                "url": "http://B01.com",
                "events_in_kind": "$40",
                "total": "$70",
                "digital_revenue": "$0"
            }
        ],
        "all-time": [
            {
                "events_revenue": "$4",
                "digital_in_kind": "$0",
                "sponsor": "Donor A",
                "url": "http://A01.com",
                "events_in_kind": "$0",
                "total": "$9",
                "digital_revenue": "$5"
            },
            {
                "events_revenue": "$30",
                "digital_in_kind": "$20",
                "sponsor": "Donor B",
                "url": "http://B01.com",
                "events_in_kind": "$40",
                "total": "$90",
                "digital_revenue": "$0"
            }
        ]
    }
    """
    actual = convert_sponsors(opportunities=opportunities, accounts=accounts)
    assert json.loads(actual) == json.loads(expected)


def test_sponsors_sort_order():
    """
    Confirm that sponsors are sorted by their name, not ID.
    """
    opportunities = DataFrame({
        "AccountId": ["A01", "B01", "C01"],
        "Amount": [20, 20, 20],
        "CloseDate": ['2009-01-02', '2009-01-02', '2009-01-02'],
        "RecordTypeId": ['01216000001IhIEAA0', '01216000001IhIEAA0',
            '01216000001IhIEAA0'],
        "Type": ['Standard', 'Standard', 'Standard'],
    })

    accounts = DataFrame({
        "AccountId": ["A01", "B01", "C01"],
        "Text_For_Donor_Wall__c": ["Donor Z", "Donor A", "Donor B"],
        "Website": ['http://Z01.com', 'http://A01.com', 'http://B01.com'],
    })

    expected = """
    {
        "2009": [
            {
                "url": "http://A01.com",
                "events_in_kind": "$0",
                "digital_revenue": "$20",
                "digital_in_kind": "$0",
                "sponsor": "Donor A",
                "events_revenue": "$0",
                "total": "$20"
            },
            {
                "url": "http://B01.com",
                "events_in_kind": "$0",
                "digital_revenue": "$20",
                "digital_in_kind": "$0",
                "sponsor": "Donor B",
                "events_revenue": "$0",
                "total": "$20"
            },
            {
                "url": "http://Z01.com",
                "events_in_kind": "$0",
                "digital_revenue": "$20",
                "digital_in_kind": "$0",
                "sponsor": "Donor Z",
                "events_revenue": "$0",
                "total": "$20"
            }
        ],
        "all-time": [
            {
                "url": "http://A01.com",
                "events_in_kind": "$0",
                "digital_revenue": "$20",
                "digital_in_kind": "$0",
                "sponsor": "Donor A",
                "events_revenue": "$0",
                "total": "$20"
            },
            {
                "url": "http://B01.com",
                "events_in_kind": "$0",
                "digital_revenue": "$20",
                "digital_in_kind": "$0",
                "sponsor": "Donor B",
                "events_revenue": "$0",
                "total": "$20"
            },
            {
                "url": "http://Z01.com",
                "events_in_kind": "$0",
                "digital_revenue": "$20",
                "digital_in_kind": "$0",
                "sponsor": "Donor Z",
                "events_revenue": "$0",
                "total": "$20"
            }
        ]
    }
    """
    actual = convert_sponsors(opportunities=opportunities, accounts=accounts)
    assert json.loads(actual) == json.loads(expected)


def test__extract_and_map():
    """
    Check that the transform works as expected.
    """
    # this is the kind of list that will be returned from SF:
    test_list = [{
        u'Text_For_Donor_Wall__c': u'Mark Zlinger',
        u'Name': u'Zlinger Account',
        u'attributes': {
            u'type': u'Account',
            u'url': u'/services/data/v33.0/sobjects/Account/0011700000C46BMAAZ'
            },
        u'npo02__LastMembershipLevel__c': u"Editor's Circle"},
        {
        u'Text_For_Donor_Wall__c': u'Mark Olinger',
        u'Name': u'Olinger Account',
        u'attributes': {
            u'type': u'Account',
            u'url': u'/services/data/v33.0/sobjects/Account/0011700000C46BMAAZ'
             },
        u'npo02__LastMembershipLevel__c': u"Editor's Circle"
        }]
    key = 'Text_For_Donor_Wall__c'
    value = 'npo02__LastMembershipLevel__c'
    # this is what we want:
    expected = {
            u'Olinger Account:Mark Olinger': u"Editor's Circle",
            u'Zlinger Account:Mark Zlinger': u"Editor's Circle"
            }
    sort = 'Name'
    actual = _extract_and_map(test_list, key, value, sort)
    assert expected == actual


def test__invert_and_aggregate():
    """
    Check that the transform works as expected.
    """
    input = {u'Olinger Account:Mark Olinger': u"Editor's Circle"}
    expected = {
            u"Editor's Circle":
            [u'Olinger Account:Mark Olinger']
            }
    actual = _invert_and_aggregate(input)
    assert expected == actual


def test__sort_circle():
    input = {
            u"Editor's Circle": [
                u'Zlinger Account:Mark Zlinger',
                u'Alinger Account:Mark Alinger',
                u'Blinger Account:Mark Blinger'
                ],
            u"Chairman's Circle": [
                u"Baz", "Foo", "Bar",
                ]
            }
    expected = {
            u"Editor's Circle": [
                u'Alinger Account:Mark Alinger',
                u'Blinger Account:Mark Blinger',
                u'Zlinger Account:Mark Zlinger'
                ],
            u"Chairman's Circle": [
                'Bar', 'Baz', 'Foo',
                ]
            }
    actual = _sort_circle(input)
    assert expected == actual


def test__strip_sort_key():
    input = {
            u"Editor's Circle": [
                u'Alinger Account:Mark Alinger',
                u'Blinger Account:Mark Blinger',
                u'Zlinger Account:Mark Zlinger'
                ],
            u"Chairman's Circle": [
                'Bar', 'Baz', 'Foo',
                ]
            }
    expected = {
            u"Editor's Circle": [
                u'Mark Alinger',
                u'Mark Blinger',
                u'Mark Zlinger'
                ],
            u"Chairman's Circle": [
                'Bar', 'Baz', 'Foo',
                ]
            }
    actual = _strip_sort_key(input)
    assert expected == actual


def test_clean_url():
    """
    Test that the function that cleans up URLs works
    as expected.
    """

    input = 'NULL'
    actual = clean_url(input)
    assert actual == ''

    input = 'www.abc.org'
    actual = clean_url(input)
    assert actual == 'http://www.abc.org'

    input = ''
    actual = clean_url(input)
    assert actual == ''

    input = 'http://'
    actual = clean_url(input)
    assert actual == ''
