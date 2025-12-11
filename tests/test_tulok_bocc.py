from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import BOARD
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.tulok_bocc import TulokBoccSpider

# Load local JSON file for testing
test_response = file_response(
    join(dirname(__file__), "files", "tulok_bocc.json"),
    url="https://tulsacook.api.civicclerk.com/v1/Events?$filter=categoryId+in+(26,40)",
)
spider = TulokBoccSpider()

# Freeze time for consistent test results
freezer = freeze_time("2025-12-02")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_first_item_properties():
    item = parsed_items[0]
    assert item["title"] == "Board of County Commissioners Regular Meeting"
    assert item["start"] == datetime(2025, 12, 9, 9, 0)
    assert item["end"] == datetime(2025, 12, 9, 11, 0)
    assert item["status"] == "tentative"
    assert item["location"] == {
        "name": "Board of County Commissioners",
        "address": "500 S Denver Ave Room 100 Tulsa, OK, 74103",
    }
    # Links
    assert len(item["links"]) == 2
    assert item["links"][0]["title"] == "Agenda"
    assert item["links"][0]["href"].startswith("https://tulsacook.portal.civicclerk.com/")


def test_title():
    for item in parsed_items:
        assert item["title"] in [
            "Board of County Commissioners Regular Meeting",
            "Board of County Commissioners Special Meeting",
            "Budget Workshop",
        ]


def test_description():
    for item in parsed_items:
        assert isinstance(item["description"], str)


def test_start():
    for item in parsed_items:
        assert isinstance(item["start"], datetime)


def test_end():
    for item in parsed_items:
        assert item["end"] is None or isinstance(item["end"], datetime)


def test_time_notes():
    for item in parsed_items:
        assert isinstance(item["time_notes"], str)


def test_id_and_status():
    for item in parsed_items:
        assert item["id"]
        assert item["status"] in ["tentative", "confirmed", "cancelled", "passed"]


def test_location():
    for item in parsed_items:
        assert item["location"]["name"] == "Board of County Commissioners"
        assert isinstance(item["location"]["address"], str)


def test_source():
    for item in parsed_items:
        assert item["source"].startswith("https://tulsacook.api.civicclerk.com/")


def test_links():
    for item in parsed_items:
        assert isinstance(item["links"], list)
        for link in item["links"]:
            assert "href" in link and "title" in link
            assert link["href"].startswith("https://tulsacook.portal.civicclerk.com/")


def test_classification():
    for item in parsed_items:
        assert item["classification"] == BOARD


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False
