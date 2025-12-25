import json
from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time
from scrapy import Request

from city_scrapers.spiders import tulsa_city

TulokAuditCommitteeSpider = tulsa_city.TulokAuditCommitteeSpider

test_response = file_response(
    join(dirname(__file__), "files", "tulsa_city_upcoming_meetings.html"),
    url="https://tulsa-ok.granicus.com/ViewPublisher.php?view_id=4",
)

with open(join(dirname(__file__), "files", "tulok_audit_committee.json")) as f:
    api_data = json.load(f)

test_response.request = Request(
    url=test_response.url,
    meta={"api_data": api_data},
)


@pytest.fixture
def parsed_items():
    spider = TulokAuditCommitteeSpider()
    with freeze_time("2025-12-09"):
        return [item for item in spider.parse(test_response)]


def test_count(parsed_items):
    assert len(parsed_items) == 152


def test_title(parsed_items):
    assert parsed_items[0]["title"] == "Audit Committee of the City of Tulsa (AUDIT)"


def test_description(parsed_items):
    assert parsed_items[0]["description"] == ""


def test_classification(parsed_items):
    assert parsed_items[0]["classification"] == COMMITTEE


def test_start(parsed_items):
    assert parsed_items[0]["start"] == datetime(2025, 11, 20, 11, 30)


def test_end(parsed_items):
    assert parsed_items[0]["end"] is None


def test_time_notes(parsed_items):
    assert parsed_items[0]["time_notes"] == ""


def test_id(parsed_items):
    assert (
        parsed_items[0]["id"]
        == "tulok_audit_committee/202511201130/x/audit_committee_of_the_city_of_tulsa_audit_"  # noqa
    )


def test_status(parsed_items):
    assert parsed_items[0]["status"] == PASSED


def test_location(parsed_items):
    assert parsed_items[0]["location"] == {
        "name": "3rd Floor North Presentation Room, City Hall at One Technology Center",
        "address": "175 E 2nd St, Tulsa, OK 74103",
    }


def test_source(parsed_items):
    assert (
        parsed_items[0]["source"]
        == "https://www.cityoftulsa.org/government/meeting-agendas/"
    )


def test_links(parsed_items):
    assert len(parsed_items[0]["links"]) == 1
    assert parsed_items[0]["links"] == [
        {
            "href": "https://www.cityoftulsa.org/apps/COTDisplayDocument/?DocumentType=Agenda&DocumentIdentifiers=31465",  # noqa
            "title": "Agenda",
        },
    ]


def test_all_day(parsed_items):
    assert parsed_items[0]["all_day"] is False
