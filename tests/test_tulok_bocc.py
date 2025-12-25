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

# Load HTML file for testing info page parsing
info_page_response = file_response(
    join(dirname(__file__), "files", "tulok_bocc.html"),
    url="https://www2.tulsacounty.org/Legacy/agendasdetail_civic.aspx?entity=BOCC",
)

spider = TulokBoccSpider()

# Parse the info page first to extract time notes
list(spider.parse_info_page(info_page_response))

# Freeze time for consistent test results
freezer = freeze_time("2025-12-02")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_first_item_properties():
    item = parsed_items[0]
    assert item["title"] == "Board of County Commissioners"
    assert item["start"] == datetime(2025, 12, 8, 9, 30)
    assert item["end"] == datetime(2025, 12, 8, 11, 30)
    assert item["status"] == "tentative"
    assert item["location"] == {
        "name": "Tulsa County Headquarters Building",
        "address": "Room 132 218 W 6th ST Tulsa, OK, 74119",
    }
    # Links
    assert len(item["links"]) == 3
    assert item["links"][0]["title"] == "Agenda"
    assert (
        item["links"][0]["href"]
        == "https://tulsacook.portal.civicclerk.com/event/2182/files/agenda/9404"
    )  # noqa


def test_title_values():
    for item in parsed_items:
        assert item["title"] in [
            "Board of County Commissioners",
            "Board of County Commissioners Special Meeting",
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
        assert "BOCC meets every Monday" in item["time_notes"]
        assert "9:30 a.m." in item["time_notes"]


def test_parse_info_page():
    """Test that time notes are correctly extracted from the info page HTML."""
    test_spider = TulokBoccSpider()
    list(test_spider.parse_info_page(info_page_response))
    assert "BOCC meets every Monday" in test_spider.time_notes
    assert "9:30 a.m." in test_spider.time_notes
    assert "Tuesday at 8:30 a.m." in test_spider.time_notes


def test_id_and_status():
    for item in parsed_items:
        assert item["id"]
        assert item["status"] in ["tentative", "confirmed", "cancelled", "passed"]


def test_location():
    for item in parsed_items:
        assert item["location"]["name"] == "Tulsa County Headquarters Building"
        assert isinstance(item["location"]["address"], str)


def test_source():
    for item in parsed_items:
        assert (
            item["source"]
            == "https://www2.tulsacounty.org/Legacy/agendasdetail_civic.aspx?entity=BOCC%20-%20Board%20of%20County%20Commissioners"  # noqa
        )


def test_links():
    for item in parsed_items:
        assert isinstance(item["links"], list)
        for link in item["links"]:
            assert "href" in link and "title" in link
            assert link["href"].startswith("https://tulsacook.portal.civicclerk.com/")
            assert link["title"] in [
                "Agenda",
                "Agenda Packet",
                "Minutes",
                "Other",
                "Document",
            ]  # noqa
    # Future meeting (3rd item) has no published files
    assert parsed_items[2]["links"] == []


def test_classification():
    for item in parsed_items:
        assert item["classification"] == BOARD


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False
