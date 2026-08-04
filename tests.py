import json

import pandas as pd
from pandas import DataFrame

from convert import (
    _extract_and_map,
    _invert_and_aggregate,
    _sort_circle,
    _strip_sort_key,
    clean_url,
    convert_donors,
    convert_qualified_supporters,
    convert_sponsors,
    make_pretty_money,
)


def test_convert_to_json_with_empty_amount():
    """
    Verify that blank values are ignored.
    """

    opportunities = DataFrame(
        {
            "AccountId": ["A01", "B01", "A01", "B01"],
            "Amount": [10.0, 20.0, 30.0, ""],
            "CloseDate": ["2009-01-02", "2009-01-03", "2009-01-04", "2010-01-02"],
        }
    )

    accounts = DataFrame(
        {"AccountId": ["A01", "B01"], "Text_For_Donor_Wall__c": ["Donor A", "Donor B"]}
    )
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

    opportunities = DataFrame(
        {
            "AccountId": ["A01", "B01", "A01", "B01"],
            "Amount": [10.0, 20.0, 30.0, 4000.0],
            "CloseDate": ["2009-01-02", "2009-01-03", "2009-01-04", "2010-01-02"],
        }
    )

    accounts = DataFrame(
        {"AccountId": ["A01", "B01"], "Text_For_Donor_Wall__c": ["Donor A", "Donor B"]}
    )
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

    opportunities = DataFrame(
        {
            "AccountId": ["A01", "B01", "A01", "B01"],
            "Amount": [5.0, 20.0, 4.0, 4000.0],
            "CloseDate": ["2009-01-02", "2009-01-03", "2009-01-04", "2010-01-02"],
        }
    )

    accounts = DataFrame(
        {"AccountId": ["A01", "B01"], "Text_For_Donor_Wall__c": ["Donor A", "Donor B"]}
    )
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

    opportunities = DataFrame(
        {
            "AccountId": ["A01", "B01", "A01", "B01"],
            "Amount": [5.0, 20.0, 4.0, 4000.0],
            "CloseDate": ["2009-01-02", "2009-01-03", "2009-01-04", "2010-01-02"],
        }
    )

    accounts = DataFrame(
        {"AccountId": ["A01", "B01"], "Text_For_Donor_Wall__c": ["Donor A", "Donor B"]}
    )
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
    expected = "$4,000"
    actual = make_pretty_money(input)
    assert actual == expected


def test_make_pretty_money_rounding():
    """
    Check that rounding works.
    """

    input = 4.50
    expected = "$5"
    actual = make_pretty_money(input)
    assert actual == expected


def test_make_pretty_money_round_down():
    """
    Check that rounding works.
    """

    input = 4.49
    expected = "$4"
    actual = make_pretty_money(input)
    assert actual == expected


def test_sponsors():
    """
    Do an end-to-end sponsor check.
    """

    opportunities = DataFrame(
        {
            "AccountId": ["A01", "B01", "A01", "B01", "B01"],
            "Amount": [5.0, 20.0, 4.0, 40.0, 30.0],
            "CloseDate": [
                "2009-01-02",
                "2009-01-03",
                "2009-01-04",
                "2010-01-02",
                "2010-01-02",
            ],
            "RecordTypeId": [
                "01216000001IhIEAA0",
                "01216000001IhIEAA0",
                "01216000001IhmxAAC",
                "01216000001IhmxAAC",
                "01216000001IhmxAAC",
            ],
            "Type": ["Standard", "In-Kind", "", "In-Kind", ""],
        }
    )

    accounts = DataFrame(
        {
            "AccountId": ["A01", "B01"],
            "Text_For_Donor_Wall__c": ["Donor A", "Donor B"],
            "Website": ["http://A01.com", "http://B01.com"],
        }
    )

    expected = """{
        "2009": [
            {
                "events_revenue": "$4",
                "digital_in_kind": "$0",
                "sponsor": "Donor A",
                "url": "http://A01.com",
                "events_in_kind": "$0",
                "total": "$9",
                "digital_revenue": "$5",
                "business_membership": "$0",
                "licensing" : "$0"
            },
            {
                "events_revenue": "$0",
                "digital_in_kind": "$20",
                "sponsor": "Donor B",
                "url": "http://B01.com",
                "events_in_kind": "$0",
                "total": "$20",
                "digital_revenue": "$0",
                "business_membership": "$0",
                "licensing" : "$0"
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
                "digital_revenue": "$0",
                "business_membership": "$0",
                "licensing" : "$0"
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
                "digital_revenue": "$5",
                "business_membership": "$0",
                "licensing" : "$0"
            },
            {
                "events_revenue": "$30",
                "digital_in_kind": "$20",
                "sponsor": "Donor B",
                "url": "http://B01.com",
                "events_in_kind": "$40",
                "total": "$90",
                "digital_revenue": "$0",
                "business_membership": "$0",
                "licensing" : "$0"
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
    opportunities = DataFrame(
        {
            "AccountId": ["A01", "B01", "C01"],
            "Amount": [20.0, 20.0, 20.0],
            "CloseDate": ["2009-01-02", "2009-01-02", "2009-01-02"],
            "RecordTypeId": [
                "01216000001IhIEAA0",
                "01216000001IhIEAA0",
                "01216000001IhIEAA0",
            ],
            "Type": ["Standard", "Standard", "Standard"],
        }
    )

    accounts = DataFrame(
        {
            "AccountId": ["A01", "B01", "C01"],
            "Text_For_Donor_Wall__c": ["Donor Z", "Donor A", "Donor B"],
            "Website": ["http://Z01.com", "http://A01.com", "http://B01.com"],
        }
    )

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
                "business_membership": "$0",
                "licensing" : "$0",
                "total": "$20"
            },
            {
                "url": "http://B01.com",
                "events_in_kind": "$0",
                "digital_revenue": "$20",
                "digital_in_kind": "$0",
                "sponsor": "Donor B",
                "events_revenue": "$0",
                "business_membership": "$0",
                "licensing" : "$0",
                "total": "$20"
            },
            {
                "url": "http://Z01.com",
                "events_in_kind": "$0",
                "digital_revenue": "$20",
                "digital_in_kind": "$0",
                "sponsor": "Donor Z",
                "events_revenue": "$0",
                "business_membership": "$0",
                "licensing" : "$0",
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
                "business_membership": "$0",
                "licensing" : "$0",
                "total": "$20"
            },
            {
                "url": "http://B01.com",
                "events_in_kind": "$0",
                "digital_revenue": "$20",
                "digital_in_kind": "$0",
                "sponsor": "Donor B",
                "events_revenue": "$0",
                "business_membership": "$0",
                "licensing" : "$0",
                "total": "$20"
            },
            {
                "url": "http://Z01.com",
                "events_in_kind": "$0",
                "digital_revenue": "$20",
                "digital_in_kind": "$0",
                "sponsor": "Donor Z",
                "events_revenue": "$0",
                "business_membership": "$0",
                "licensing" : "$0",
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
    test_list = [
        {
            "Text_For_Donor_Wall__c": "Mark Zlinger",
            "Name": "Zlinger Account",
            "attributes": {
                "type": "Account",
                "url": "/services/data/v33.0/sobjects/Account/0011700000C46BMAAZ",
            },
            "npo02__LastMembershipLevel__c": "Editor's Circle",
        },
        {
            "Text_For_Donor_Wall__c": "Mark Olinger",
            "Name": "Olinger Account",
            "attributes": {
                "type": "Account",
                "url": "/services/data/v33.0/sobjects/Account/0011700000C46BMAAZ",
            },
            "npo02__LastMembershipLevel__c": "Editor's Circle",
        },
    ]
    key = "Text_For_Donor_Wall__c"
    value = "npo02__LastMembershipLevel__c"
    # this is what we want:
    expected = {
        "Olinger Account:Mark Olinger": "Editor's Circle",
        "Zlinger Account:Mark Zlinger": "Editor's Circle",
    }
    sort = "Name"
    actual = _extract_and_map(test_list, key, value, sort)
    assert expected == actual


def test__invert_and_aggregate():
    """
    Check that the transform works as expected.
    """
    input = {"Olinger Account:Mark Olinger": "Editor's Circle"}
    expected = {"Editor's Circle": ["Olinger Account:Mark Olinger"]}
    actual = _invert_and_aggregate(input)
    assert expected == actual


def test__sort_circle():
    """
    Check that circles are sorted by account name.
    """

    input = {
        "Editor's Circle": [
            "Zlinger Account:Mark Zlinger",
            "Alinger Account:Mark Alinger",
            "Blinger Account:Mark Blinger",
        ],
        "Chairman's Circle": ["Baz", "Foo", "Bar"],
    }
    expected = {
        "Editor's Circle": [
            "Alinger Account:Mark Alinger",
            "Blinger Account:Mark Blinger",
            "Zlinger Account:Mark Zlinger",
        ],
        "Chairman's Circle": ["Bar", "Baz", "Foo"],
    }
    actual = _sort_circle(input)
    assert expected == actual


def test__strip_sort_key():
    """
    Make sure they key used to sort data is stripped out before being
    sent down the pipe.
    """
    input = {
        "Editor's Circle": [
            "Alinger Account:Mark Alinger",
            "Blinger Account:Mark Blinger",
            "Zlinger Account:Mark Zlinger",
        ],
        "Chairman's Circle": ["Bar", "Baz", "Foo"],
    }
    expected = {
        "Editor's Circle": ["Mark Alinger", "Mark Blinger", "Mark Zlinger"],
        "Chairman's Circle": ["Bar", "Baz", "Foo"],
    }
    actual = _strip_sort_key(input)
    assert expected == actual


def test_clean_url():
    """
    Test that the function that cleans up URLs works
    as expected.
    """

    input = "NULL"
    actual = clean_url(input)
    assert actual == ""

    input = "www.abc.org"
    actual = clean_url(input)
    assert actual == "http://www.abc.org"

    input = ""
    actual = clean_url(input)
    assert actual == ""

    input = "http://"
    actual = clean_url(input)
    assert actual == ""


# The window is anchored to a fixed past date, not today, so these assertions
# both stay stable over time and fail if `as_of` is ever ignored.
AS_OF = "2024-01-15"
_ANCHOR = pd.Timestamp(AS_OF)


def _days_before(days):
    return (_ANCHOR - pd.Timedelta(days=days)).strftime("%Y-%m-%d")


IN_WINDOW = _days_before(30)
WINDOW_EDGE_IN = _days_before(1825)
WINDOW_EDGE_OUT = _days_before(1826)
LONG_AGO = _days_before(3000)


def _run(donor_opps=None, sponsor_opps=None, accounts=None):
    return json.loads(
        convert_qualified_supporters(
            donor_opps=donor_opps,
            sponsor_opps=sponsor_opps,
            accounts=accounts,
            as_of=AS_OF,
        )
    )


def test_qualified_supporters_tiers():
    """
    Each tier qualifies on its own, both can apply at once, and an account
    clearing neither is absent from the file.
    """
    donor_opps = DataFrame(
        {
            "AccountId":   ["A1",            "A2",            "A3",            "A4"],
            "Amount":      [1000.0,          100000.0,        100000.0,        999.0],
            "Newsroom__c": ["Texas Tribune"] * 4,
            "CloseDate":   [IN_WINDOW,       LONG_AGO,        IN_WINDOW,       IN_WINDOW],
        }
    )
    accounts = DataFrame(
        {
            "AccountId": ["A1", "A2", "A3", "A4"],
            "Text_For_Donor_Wall__c": [
                "Supporter A1", "Supporter A2", "Supporter A3", "Supporter A4"
            ],
        }
    )
    actual = _run(donor_opps=donor_opps, accounts=accounts)
    by_attr = {s["attribution"]: s for s in actual["supporters"]}

    assert by_attr["Supporter A1"]["tiers_by_newsroom"] == {"Texas Tribune": ["recent"]}
    assert by_attr["Supporter A2"]["tiers_by_newsroom"] == {"Texas Tribune": ["lifetime"]}
    assert by_attr["Supporter A3"]["tiers_by_newsroom"] == {
        "Texas Tribune": ["recent", "lifetime"]
    }
    assert "Supporter A4" not in by_attr


def test_qualified_supporters_exact_thresholds():
    """
    Both thresholds are inclusive: exactly $1,000 and exactly $100,000
    qualify, a dollar under either does not.
    """
    donor_opps = DataFrame(
        {
            "AccountId":   ["B1",      "B2",      "B3",      "B4"],
            "Amount":      [1000.0,    999.0,     100000.0,  99999.0],
            "Newsroom__c": ["Texas Tribune"] * 4,
            "CloseDate":   [IN_WINDOW, IN_WINDOW, LONG_AGO,  LONG_AGO],
        }
    )
    accounts = DataFrame(
        {
            "AccountId": ["B1", "B2", "B3", "B4"],
            "Text_For_Donor_Wall__c": [
                "Supporter B1", "Supporter B2", "Supporter B3", "Supporter B4"
            ],
        }
    )
    actual = _run(donor_opps=donor_opps, accounts=accounts)
    assert sorted(s["attribution"] for s in actual["supporters"]) == [
        "Supporter B1",
        "Supporter B3",
    ]


def test_qualified_supporters_window_boundary():
    """
    An opportunity exactly 1,825 days old is inside the window; 1,826 days is
    outside it. The out-of-window gift still counts toward the lifetime total,
    which is why C3 qualifies on the lifetime tier alone.
    """
    donor_opps = DataFrame(
        {
            "AccountId":   ["C1",            "C2",             "C3"],
            "Amount":      [1000.0,          1000.0,           100000.0],
            "Newsroom__c": ["Texas Tribune"] * 3,
            "CloseDate":   [WINDOW_EDGE_IN,  WINDOW_EDGE_OUT,  WINDOW_EDGE_OUT],
        }
    )
    accounts = DataFrame(
        {
            "AccountId": ["C1", "C2", "C3"],
            "Text_For_Donor_Wall__c": ["Supporter C1", "Supporter C2", "Supporter C3"],
        }
    )
    actual = _run(donor_opps=donor_opps, accounts=accounts)
    by_attr = {s["attribution"]: s for s in actual["supporters"]}

    assert by_attr["Supporter C1"]["tiers_by_newsroom"] == {"Texas Tribune": ["recent"]}
    assert "Supporter C2" not in by_attr
    assert by_attr["Supporter C3"]["tiers_by_newsroom"] == {"Texas Tribune": ["lifetime"]}


def test_qualified_supporters_per_newsroom_independence():
    """
    Tiers are evaluated per newsroom, never cumulatively across them. D1 clears
    a different tier in each newsroom; D2's $500 + $600 across two newsrooms
    clears nothing.
    """
    donor_opps = DataFrame(
        {
            "AccountId":   ["D1",            "D1",       "D2",            "D2"],
            "Amount":      [1000.0,          100000.0,   500.0,           600.0],
            "Newsroom__c": ["Texas Tribune", "Austin",   "Texas Tribune", "Austin"],
            "CloseDate":   [IN_WINDOW,       LONG_AGO,   IN_WINDOW,       IN_WINDOW],
        }
    )
    accounts = DataFrame(
        {
            "AccountId": ["D1", "D2"],
            "Text_For_Donor_Wall__c": ["Supporter D1", "Supporter D2"],
        }
    )
    actual = _run(donor_opps=donor_opps, accounts=accounts)
    by_attr = {s["attribution"]: s for s in actual["supporters"]}

    assert by_attr["Supporter D1"]["tiers_by_newsroom"] == {
        "Texas Tribune": ["recent"],
        "Austin": ["lifetime"],
    }
    assert "Supporter D2" not in by_attr


def test_qualified_supporters_donor_and_sponsor_stay_separate():
    """
    The same account qualifying as both a donor and a sponsor produces two
    entries, one per source. Sponsors carry no account_type even when the
    Salesforce record is a Household — that keeps the consumer from routing a
    sponsor to its personal-name matching path.
    """
    opps = DataFrame(
        {
            "AccountId":   ["E1"],
            "Amount":      [1000.0],
            "Newsroom__c": ["Texas Tribune"],
            "CloseDate":   [IN_WINDOW],
        }
    )
    accounts = DataFrame(
        {
            "AccountId": ["E1"],
            "Text_For_Donor_Wall__c": ["Supporter E1"],
            "Type": ["Household"],
        }
    )
    actual = _run(donor_opps=opps, sponsor_opps=opps.copy(), accounts=accounts)
    by_source = {s["source"]: s for s in actual["supporters"]}

    assert len(actual["supporters"]) == 2
    assert by_source["donor"]["attribution"] == "Supporter E1"
    assert by_source["sponsor"]["attribution"] == "Supporter E1"
    assert by_source["donor"]["account_type"] == "Household"
    assert by_source["sponsor"]["account_type"] is None


def test_qualified_supporters_defensive_newsroom_filter():
    """
    A Newsroom__c value outside the canonical three — new picklist entry, stale
    data, SOQL drift — is dropped before aggregation.
    """
    donor_opps = DataFrame(
        {
            "AccountId":   ["F1",            "F2"],
            "Amount":      [1000.0,          1000.0],
            "Newsroom__c": ["Texas Tribune", "Bogus"],
            "CloseDate":   [IN_WINDOW,       IN_WINDOW],
        }
    )
    accounts = DataFrame(
        {
            "AccountId": ["F1", "F2"],
            "Text_For_Donor_Wall__c": ["Supporter F1", "Supporter F2"],
        }
    )
    actual = _run(donor_opps=donor_opps, accounts=accounts)
    assert [s["attribution"] for s in actual["supporters"]] == ["Supporter F1"]


def test_qualified_supporters_account_type_missing_or_empty():
    """
    No Type column (older fixtures, SOQL drift) or an empty string yields a null
    account_type. The consumer defaults null to organization.
    """
    donor_opps = DataFrame(
        {
            "AccountId":   ["G1"],
            "Amount":      [1000.0],
            "Newsroom__c": ["Texas Tribune"],
            "CloseDate":   [IN_WINDOW],
        }
    )
    accounts_no_col = DataFrame(
        {"AccountId": ["G1"], "Text_For_Donor_Wall__c": ["Supporter G1"]}
    )
    actual = _run(donor_opps=donor_opps, accounts=accounts_no_col)
    assert actual["supporters"][0]["account_type"] is None

    accounts_empty = DataFrame(
        {
            "AccountId": ["G1"],
            "Text_For_Donor_Wall__c": ["Supporter G1"],
            "Type": [""],
        }
    )
    actual = _run(donor_opps=donor_opps, accounts=accounts_empty)
    assert actual["supporters"][0]["account_type"] is None


def test_qualified_supporters_empty_inputs():
    """
    No opportunities on either side returns an empty supporter list with the
    metadata block intact. walls.py checks this list and skips the S3 push
    rather than overwriting a good file with an empty one.
    """
    actual = _run(accounts=DataFrame())
    assert actual["supporters"] == []
    assert actual["metadata"]["window_days"] == 1825


def test_qualified_supporters_metadata_block():
    """
    Metadata carries the thresholds and window so consumers read the numbers
    from here rather than inferring them from the tier names.
    """
    donor_opps = DataFrame(
        {
            "AccountId":   ["H1"],
            "Amount":      [1000.0],
            "Newsroom__c": ["Texas Tribune"],
            "CloseDate":   [IN_WINDOW],
        }
    )
    accounts = DataFrame(
        {"AccountId": ["H1"], "Text_For_Donor_Wall__c": ["Supporter H1"]}
    )
    metadata = _run(donor_opps=donor_opps, accounts=accounts)["metadata"]

    assert metadata["window_days"] == 1825
    assert metadata["recent_threshold"] == 1000
    assert metadata["lifetime_threshold"] == 100000
    assert metadata["in_kind_included"] is True
    assert metadata["donor_record_types"] == ["Membership"]
    assert metadata["newsrooms"] == ["Texas Tribune", "Austin", "Waco Bridge"]
    assert metadata["generated_at"].endswith("Z")
    assert len(metadata["generated_at"]) == 20  # YYYY-MM-DDTHH:MM:SSZ
