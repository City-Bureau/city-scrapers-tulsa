from datetime import datetime
from os.path import dirname, join

from city_scrapers_core.constants import PASSED, COMMITTEE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time
import json
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

spider = TulokAuditCommitteeSpider()

freezer = freeze_time("2025-12-09")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_count():
    assert len(parsed_items) == 152


def test_title():
    assert (
        parsed_items[0]["title"]
        == "Audit Committee of the City of Tulsa (AUDIT)"
    )


def test_description():
    assert parsed_items[0]["description"] == ""


def test_classification():
    assert parsed_items[0]["classification"] == COMMITTEE


def test_start():
    assert parsed_items[0]["start"] == datetime(2025, 11, 20, 11, 30)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    assert (
        parsed_items[0]["id"]
        == "tulok_audit_committee/202511201130/x/audit_committee_of_the_city_of_tulsa_audit_"  # noqa
    )


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "3rd Floor North Presentation Room, City Hall at One Technology Center",
        "address": "175 E 2nd St, Tulsa, OK 74103",
    }


def test_source():
    assert (
        parsed_items[0]["source"]
        == "https://www.cityoftulsa.org/government/meeting-agendas/"
    )


def test_links():
    assert len(parsed_items[0]["links"]) == 1
    assert parsed_items[0]["links"] == [
        {
            "href": "https://www.cityoftulsa.org/apps/COTDisplayDocument/?DocumentType=Agenda&DocumentIdentifiers=31465",  # noqa
            "title": "Agenda",
        },
    ]


def test_all_day():
    assert parsed_items[0]["all_day"] is False
