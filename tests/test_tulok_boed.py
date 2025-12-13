"""
Tests for tulok_boed spider.
"""
from datetime import datetime
from os.path import dirname, join

from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.tulok_boed import TulokBoedSpider

test_response = file_response(
    join(dirname(__file__), "files", "tulok_boed.json"),
    url="https://tulsaschools.diligent.community/Services/MeetingsService.svc/meetings?from=2024-12-01&to=9999-12-31",  # noqa
)
spider = TulokBoedSpider()

freezer = freeze_time("2025-12-09")
freezer.start()
parsed_items = [item for item in spider.parse(test_response)]
freezer.stop()


def test_items_scraped():
    """Verify items were scraped."""
    assert len(parsed_items) > 0, "No items scraped"


def test_required_fields():
    """Verify all required Meeting fields are present."""
    required_fields = [
        "title",
        "description",
        "classification",
        "start",
        "end",
        "all_day",
        "time_notes",
        "location",
        "links",
        "source",
        "status",
        "id",
    ]
    for item in parsed_items:
        for field in required_fields:
            assert field in item, f"Missing field: {field}"


def test_classification():
    """Verify all items have BOARD classification."""
    for item in parsed_items:
        assert item["classification"] == "Board"


def test_location_structure():
    """Verify location has correct structure."""
    for item in parsed_items:
        assert "name" in item["location"]
        assert "address" in item["location"]
        assert item["location"]["address"] != ""


def test_links_structure():
    """Verify links have correct structure."""
    for item in parsed_items:
        assert isinstance(item["links"], list)
        for link in item["links"]:
            assert "href" in link
            assert "title" in link


def test_start_datetime_format():
    """Verify start datetime is a datetime object."""
    for item in parsed_items:
        assert item["start"] is not None
        assert isinstance(item["start"], datetime)


def test_status_values():
    """Verify status is one of valid values."""
    valid_statuses = ["tentative", "confirmed", "passed", "cancelled"]
    for item in parsed_items:
        assert item["status"] in valid_statuses


def test_id_format():
    """Verify ID follows expected format."""
    for item in parsed_items:
        assert item["id"].startswith("tulok_boed/")


def test_source_url():
    """Verify source URLs are valid."""
    for item in parsed_items:
        assert item["source"].startswith("https://tulsaschools.diligent.community/")
