"""
Tests for tulok_boed spider.
"""

from datetime import datetime
from os.path import dirname, join

from city_scrapers_core.constants import BOARD
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

parsed_item = parsed_items[0]


def test_count():
    assert len(parsed_items) == 50


def test_title():
    assert parsed_item["title"] == "Regular Meeting"


def test_description():
    assert parsed_item["description"] == ""


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_start():
    assert parsed_item["start"] == datetime(2026, 12, 14, 17, 30)


def test_end():
    assert parsed_item["end"] is None


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"] == "tulok_boed/202612141730/x/regular_meeting"


def test_status():
    assert parsed_item["status"] == "tentative"


def test_location():
    assert parsed_item["location"] == {
        "name": "Cheryl Selman Room, Charles C. Mason Education Service Center",
        "address": "3027 S. New Haven Ave., Tulsa OK",
    }


def test_source():
    assert (
        parsed_item["source"]
        == "https://tulsaschools.diligent.community/Portal/MeetingInformation.aspx?Org=Cal&Id=213"  # noqa
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "href": "https://tulsaschools.diligent.community/Portal/MeetingInformation.aspx?Org=Cal&Id=213",  # noqa
            "title": "Agenda",
        }
    ]


def test_all_day():
    assert parsed_item["all_day"] is False
