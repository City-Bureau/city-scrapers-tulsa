"""
Tests for Tulsa City Council spider.
"""

from os.path import dirname, join

from city_scrapers_core.constants import CITY_COUNCIL, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.tulok_citycouncil import TulsaGranicusCityCouncilSpider

test_response = file_response(
    join(dirname(__file__), "files", "tulok_citycouncil.html"),
    url="https://tulsa-ok.granicus.com/ViewPublisher.php?view_id=4",
)
spider = TulsaGranicusCityCouncilSpider()

freezer = freeze_time("2025-12-05")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_meeting_count():
    """Test that the correct number of meetings are parsed."""
    # Test HTML contains 13 meetings across all years (2016-2025):
    # 2025: 2, 2024: 1, 2023: 1, 2022: 1, 2021: 1, 2020: 1, 2019: 1, 2018: 1, 2017: 2, 2016: 2
    assert len(parsed_items) == 13


def test_title():
    """Test meeting title parsing."""
    assert parsed_items[0]["title"] == "Regular Council Meeting"


def test_description():
    """Test meeting description."""
    assert parsed_items[0]["description"] == ""


def test_start():
    """Test meeting start datetime."""
    # Based on the HTML snippet: "November 19, 2025 - 5:00 PM"
    assert parsed_items[0]["start"].month == 11
    assert parsed_items[0]["start"].day == 19
    assert parsed_items[0]["start"].year == 2025
    assert parsed_items[0]["start"].hour == 17
    assert parsed_items[0]["start"].minute == 0


def test_end():
    """Test meeting end datetime."""
    assert parsed_items[0]["end"] is None


def test_time_notes():
    """Test meeting time notes."""
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    """Test meeting ID generation."""
    assert parsed_items[0]["id"] is not None
    assert "tulok_citycouncil" in parsed_items[0]["id"]


def test_status():
    """Test meeting status."""
    assert parsed_items[0]["status"] == PASSED


def test_location():
    """Test meeting location."""
    assert parsed_items[0]["location"]["name"] == "City Hall"
    assert "175 E 2nd St" in parsed_items[0]["location"]["address"]


def test_source():
    """Test meeting source URL."""
    assert (
        parsed_items[0]["source"]
        == "https://tulsa-ok.granicus.com/ViewPublisher.php?view_id=4"
    )


def test_links():
    """Test meeting links (agenda and video)."""
    links = parsed_items[0]["links"]
    assert len(links) == 2

    # Check for agenda link
    agenda_link = next((link for link in links if link["title"] == "Agenda"), None)
    assert agenda_link is not None
    assert "AgendaViewer.php" in agenda_link["href"]
    assert agenda_link["href"].startswith("https://")

    # Check for video link
    video_link = next((link for link in links if link["title"] == "Video"), None)
    assert video_link is not None
    assert "MediaPlayer.php" in video_link["href"]
    assert video_link["href"].startswith("https://")


def test_classification():
    """Test meeting classification."""
    assert parsed_items[0]["classification"] == CITY_COUNCIL


def test_all_day():
    """Test all_day flag."""
    assert parsed_items[0]["all_day"] is False


def test_special_meeting():
    """Test that special meetings are properly titled."""
    # Find a special meeting in the parsed items
    special_meeting = next(
        (item for item in parsed_items if "Special" in item["title"]), None
    )
    if special_meeting:
        assert "Special" in special_meeting["title"]
        assert special_meeting["classification"] == CITY_COUNCIL
