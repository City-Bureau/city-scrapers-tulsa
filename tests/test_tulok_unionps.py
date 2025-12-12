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

parsed_items = []
# Run spider.parse() → yields only a Request
for req in spider.parse(test_response):
    board_page = file_response(
        join(dirname(__file__), "files", "tulok_unionps_board.html"),
        url="https://www.unionps.org/about/board-of-education",
    )
    # Attach main_page to meta
    board_page.meta["main_page"] = test_response
    # Call parse_board_page manually to extract meetings
    parsed_items.extend(spider.parse_board_page(board_page))


freezer.stop()


def test_first_item_properties():
    item = parsed_items[0]
    assert item["title"] == "Board of Education Meeting"
    assert item["start"] == datetime(2025, 1, 21, 19, 0)
    assert item["status"] == "passed"
    assert item["location"] == spider.meeting_location

    assert isinstance(item["description"], str)
    assert item["description"] != ""

    # Links
    assert len(item["links"]) == 4
    assert item["links"][0]["title"] == "Agenda"
    href = item["links"][0]["href"]
    assert href.startswith("https://www.unionps.org/fs/resource-manager/view/")


def test_title_values():
    allowed_titles = {
        "Board of Education Meeting",
        "Board of Education Special Meeting",
    }

    for item in parsed_items:
        assert item["title"] in allowed_titles


def test_description():
    for item in parsed_items:
        assert isinstance(item["description"], str)


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
            assert link["title"] in ["Agenda", "Minutes", "Board Report", "Video"]


def test_classification():
    for item in parsed_items:
        assert item["classification"] == BOARD


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False
