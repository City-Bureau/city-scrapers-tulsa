from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import BOARD
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.tulok_unionps import TulokUnionpsSpider

# Load local HTML file for testing
test_response = file_response(
    join(dirname(__file__), "files", "tulok_unionps.html"),
    url="https://www.unionps.org/about/board-of-education/agendas-and-minutes",
)
spider = TulokUnionpsSpider()

# Freeze time for consistent test results
freezer = freeze_time("2025-11-25")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_titles():
    # Check first few titles
    assert parsed_items[0]["title"] in [
        "Board of Education Meeting",
        "Board of Education Special Meeting",
    ]
    # All items have a title
    for item in parsed_items:
        assert item["title"]


def test_description():
    for item in parsed_items:
        assert item["description"] == ""


def test_start():
    for item in parsed_items:
        assert isinstance(item["start"], datetime)


def test_end():
    for item in parsed_items:
        assert item["end"] is None


def test_time_notes():
    for item in parsed_items:
        assert isinstance(item["time_notes"], str)
        assert item["time_notes"] != ""


def test_id_and_status():
    for item in parsed_items:
        assert item["id"]
        assert item["status"] in ["tentative", "confirmed", "cancelled", "passed"]


def test_location():
    for item in parsed_items:
        assert item["location"] == {
            "name": "Union Public Schools Administration Building",
            "address": "8506 E 61st St, Tulsa, OK 74133",
        }


def test_source():
    for item in parsed_items:
        assert (
            item["source"]
            == "https://www.unionps.org/about/board-of-education/agendas-and-minutes"
        )


def test_links():
    for item in parsed_items:
        assert isinstance(item["links"], list)
        for link in item["links"]:
            assert "href" in link and "title" in link
            assert link["href"]
            assert link["title"] in ["Agenda", "Minutes", "Board Report"]


def test_classification():
    for item in parsed_items:
        assert item["classification"] == BOARD


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False
