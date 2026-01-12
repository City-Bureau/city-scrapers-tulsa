import json
from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import COMMISSION, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time
from scrapy import Request

from city_scrapers.spiders import tulsa_city

TulokAsianAffairsSpider = tulsa_city.TulokAsianAffairsSpider

test_response = file_response(
    join(dirname(__file__), "files", "tulsa_city_upcoming_meetings.html"),
    url="https://tulsa-ok.granicus.com/ViewPublisher.php?view_id=4",
)

with open(join(dirname(__file__), "files", "tulok_asian_affairs.json")) as f:
    api_data = json.load(f)

test_response.request = Request(
    url=test_response.url,
    meta={"api_data": api_data},
)


@pytest.fixture
def parsed_items():
    spider = TulokAsianAffairsSpider()
    with freeze_time("2026-01-09"):
        return [item for item in spider.parse(test_response)]


def test_count(parsed_items):
    assert len(parsed_items) == 34


def test_title(parsed_items):
    assert parsed_items[0]["title"] == "Asian Affairs Commission (AAC)"


def test_description(parsed_items):
    assert parsed_items[0]["description"] == ""


def test_classification(parsed_items):
    assert parsed_items[0]["classification"] == COMMISSION


def test_start(parsed_items):
    assert parsed_items[0]["start"] == datetime(2026, 1, 8, 12, 0)


def test_end(parsed_items):
    assert parsed_items[0]["end"] is None


def test_time_notes(parsed_items):
    assert parsed_items[0]["time_notes"] == ""


def test_id(parsed_items):
    assert (
        parsed_items[0]["id"]
        == "tulok_asian_affairs/202601081200/x/asian_affairs_commission_aac_"
    )


def test_status(parsed_items):
    assert parsed_items[0]["status"] == PASSED


def test_location(parsed_items):
    assert parsed_items[0]["location"] == {
        "name": "Check agenda for location details",
        "address": "Check agenda for location details",
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
            "href": "https://www.cityoftulsa.org/apps/COTDisplayDocument/?DocumentType=Agenda&DocumentIdentifiers=31648",  # noqa
            "title": "Agenda",
        },
    ]


def test_all_day(parsed_items):
    assert parsed_items[0]["all_day"] is False
