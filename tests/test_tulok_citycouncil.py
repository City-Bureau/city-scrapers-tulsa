"""
Tests for Tulsa City Council spider.
"""

from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import CITY_COUNCIL, COMMITTEE, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.tulok_citycouncil import TulsaGranicusCityCouncilSpider

# Constants for test validation
# Updated to include committee meetings (Council Urban & Economic Development,
# Council Budget & Special Projects, Council Public Works)
EXPECTED_TOTAL_MEETINGS = 17
EXPECTED_HISTORICAL_MEETINGS = 13
EXPECTED_UPCOMING_MEETINGS = 4  # 2 Council + 2 Committee meetings
SOURCE_URL = "https://tulsa-ok.granicus.com/ViewPublisher.php?view_id=4"


@pytest.fixture(scope="module")
def parsed_items():
    """Parse test HTML file once and reuse for all tests."""
    test_response = file_response(
        join(dirname(__file__), "files", "tulok_citycouncil.html"),
        url=SOURCE_URL,
    )
    spider = TulsaGranicusCityCouncilSpider()
    with freeze_time("2025-12-05"):
        return list(spider.parse(test_response))


class TestMeetingCounts:
    """Test meeting counts and distribution."""

    def test_total_meeting_count(self, parsed_items):
        """Test that the correct total number of meetings are parsed."""
        # Test HTML contains:
        # - 13 historical meetings across years (2016-2025)
        # - 2 upcoming Council meetings (Regular + Special)
        # - 2 upcoming Committee meetings
        # Note: "In Progress" meetings and non-City-Council meetings (e.g., Human Rights Commission) are filtered out
        assert len(parsed_items) == EXPECTED_TOTAL_MEETINGS

    def test_historical_vs_upcoming_split(self, parsed_items):
        """Test that historical and upcoming meetings are correctly split."""
        historical = [
            item for item in parsed_items
            if item["start"].year < 2025 or (item["start"].year == 2025 and item["start"].month < 12)
        ]
        upcoming = [
            item for item in parsed_items
            if (item["start"].year == 2025 and item["start"].month == 12) or (item["start"].year == 2026)
        ]

        assert len(historical) == EXPECTED_HISTORICAL_MEETINGS
        assert len(upcoming) == EXPECTED_UPCOMING_MEETINGS
        assert len(historical) + len(upcoming) == EXPECTED_TOTAL_MEETINGS

    def test_years_coverage(self, parsed_items):
        """Test that meetings span multiple years."""
        years = {item["start"].year for item in parsed_items}
        assert len(years) >= 8  # At least 8 different years
        assert 2016 in years
        assert 2025 in years or 2026 in years


class TestMeetingStructure:
    """Test basic meeting structure and required fields."""

    def test_first_meeting_structure(self, parsed_items):
        """Test that the first meeting has all required fields with correct values."""
        meeting = parsed_items[0]

        # Basic fields
        assert meeting["title"] == "Regular Meeting"
        assert meeting["description"] == ""
        assert meeting["classification"] == CITY_COUNCIL
        assert meeting["status"] == PASSED
        assert meeting["all_day"] is False
        assert meeting["time_notes"] == ""
        assert meeting["end"] is None

        # Date/time - Based on "October 12, 2016 - 5:00 PM"
        assert meeting["start"] == datetime(2016, 10, 12, 17, 0)

        # Location
        assert meeting["location"]["name"] == "City Hall"
        assert "175 E 2nd St" in meeting["location"]["address"]

        # Source and ID
        assert meeting["source"] == SOURCE_URL
        assert meeting["id"] is not None
        assert "tulok_citycouncil" in meeting["id"]

    def test_all_meetings_have_required_fields(self, parsed_items):
        """Test that all parsed meetings have required fields."""
        for meeting in parsed_items:
            assert meeting["title"]
            assert meeting["start"] is not None
            # Classification should be either CITY_COUNCIL or COMMITTEE
            assert meeting["classification"] in [CITY_COUNCIL, COMMITTEE]
            assert meeting["source"] == SOURCE_URL
            assert meeting["location"]["name"] == "City Hall"
            assert "175 E 2nd St" in meeting["location"]["address"]
            assert meeting["all_day"] is False
            assert "tulok_citycouncil" in meeting["id"]


class TestMeetingLinks:
    """Test meeting links (agenda and video)."""

    def test_first_meeting_links(self, parsed_items):
        """Test that the first meeting has agenda and video links."""
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

    def test_upcoming_event_links_use_event_id(self, parsed_items):
        """Test that upcoming event agenda links use event_id (not clip_id)."""
        upcoming_with_agenda = next(
            (
                item for item in parsed_items
                if item["start"].year >= 2025 and item["start"].month == 12 and item["links"]
            ),
            None,
        )

        if upcoming_with_agenda:
            agenda_link = next(
                (link for link in upcoming_with_agenda["links"] if link["title"] == "Agenda"),
                None
            )
            if agenda_link:
                assert "event_id" in agenda_link["href"]
                assert agenda_link["href"].startswith("https://")


class TestMeetingFiltering:
    """Test that meetings are correctly filtered."""

    def test_special_meetings_included(self, parsed_items):
        """Test that special meetings are properly included and titled."""
        special_meetings = [item for item in parsed_items if "Special" in item["title"]]
        assert len(special_meetings) >= 1

        # All special meetings should be CITY_COUNCIL classification
        for meeting in special_meetings:
            assert meeting["classification"] == CITY_COUNCIL

        # Check specific special meeting in December exists
        special_dec = next(
            (item for item in parsed_items
             if "Council Special Meeting" in item["title"] and item["start"].month == 12),
            None
        )
        assert special_dec is not None

    def test_committee_meetings_included(self, parsed_items):
        """Test that City Council committee meetings are included."""
        # Check that committee meetings ARE in parsed items
        committee_meetings = [item for item in parsed_items if "Committee" in item["title"]]
        assert len(committee_meetings) >= 1

        # All committee meetings should have COMMITTEE classification
        for meeting in committee_meetings:
            assert meeting["classification"] == COMMITTEE

        # Verify specific committee meetings are present
        committee_names = {item["title"] for item in committee_meetings}
        # At least one of the expected committees should be present
        expected_committees = [
            "Council Urban & Economic Development Committee",
            "Council Budget & Special Projects Committee",
            "Council Public Works Committee"
        ]
        assert any(name in committee_names for name in expected_committees)

    def test_non_city_council_meetings_filtered(self, parsed_items):
        """Test that non-City-Council meetings (not committees) are filtered out."""
        # Check that "Human Rights Commission" is NOT in parsed items
        # (This is a different body, not a City Council committee)
        assert not any("Human Rights" in item["title"] for item in parsed_items)

    def test_meeting_title_variety(self, parsed_items):
        """Test that various meeting title formats are captured."""
        titles = {item["title"] for item in parsed_items}

        # Check for various title formats that exist in our test data
        assert any("Regular Council Meeting" in title for title in titles)
        assert any("Special" in title for title in titles)
        assert any("Council" in title for title in titles)
