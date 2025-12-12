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
    # Test HTML contains:
    # - 13 historical meetings across years (2016-2025)
    # - 2 upcoming Council meetings (Regular + Special)
    # Note: Committee meetings and "In Progress" meetings are filtered out
    # Total: 15 meetings
    assert len(parsed_items) == 15


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


def test_upcoming_events():
    """Test that upcoming Council meetings are parsed correctly."""
    # Find upcoming meetings (those with dates in December 2025 or later from our test HTML)
    upcoming_meetings = [
        item for item in parsed_items
        if item["start"].year == 2025 and item["start"].month == 12
        or item["start"].year == 2026
    ]

    # Should have 2 upcoming Council meetings from test HTML
    # (Regular + Special, committee meetings filtered out)
    assert len(upcoming_meetings) == 2

    # Check that all have proper structure
    for meeting in upcoming_meetings:
        assert meeting["classification"] == CITY_COUNCIL
        assert meeting["source"] == "https://tulsa-ok.granicus.com/ViewPublisher.php?view_id=4"


def test_upcoming_event_filtering():
    """Test that non-Council meetings are filtered out from upcoming events."""
    # Check that "Human Rights Commission" is NOT in parsed items
    human_rights_meeting = next(
        (item for item in parsed_items if "Human Rights" in item["title"]), None
    )
    assert human_rights_meeting is None

    # Check that committee meetings are NOT in parsed items
    committee_meeting = next(
        (item for item in parsed_items if "Committee" in item["title"]), None
    )
    assert committee_meeting is None


def test_upcoming_special_meeting():
    """Test that special meetings from upcoming events are included."""
    # Find special meetings
    special_meetings = [
        item for item in parsed_items
        if "Special" in item["title"] and item["start"].month == 12
    ]

    # Should have at least 1 special meeting in December
    assert len(special_meetings) >= 1

    # Check specific special meeting exists
    special_dec = next(
        (item for item in parsed_items
         if "Council Special Meeting" in item["title"] and item["start"].month == 12),
        None
    )
    assert special_dec is not None
    assert special_dec["classification"] == CITY_COUNCIL


def test_upcoming_event_links():
    """Test that upcoming event links are parsed correctly."""
    # Find an upcoming meeting with agenda
    upcoming_with_agenda = next(
        (
            item for item in parsed_items
            if item["start"].year >= 2025 and item["start"].month == 12
            and len(item["links"]) > 0
        ),
        None,
    )

    if upcoming_with_agenda:
        # Check that agenda link uses event_id (not clip_id)
        agenda_link = next(
            (link for link in upcoming_with_agenda["links"] if link["title"] == "Agenda"),
            None
        )
        if agenda_link:
            assert "event_id" in agenda_link["href"]
            assert agenda_link["href"].startswith("https://")


def test_all_meetings_have_required_fields():
    """Test that all parsed meetings have required fields."""
    for meeting in parsed_items:
        # Required fields
        assert meeting["title"] is not None
        assert meeting["title"] != ""
        assert meeting["start"] is not None
        assert meeting["classification"] == CITY_COUNCIL
        assert meeting["source"] == "https://tulsa-ok.granicus.com/ViewPublisher.php?view_id=4"
        assert meeting["location"]["name"] == "City Hall"
        assert "175 E 2nd St" in meeting["location"]["address"]
        assert meeting["all_day"] is False
        assert meeting["id"] is not None
        assert "tulok_citycouncil" in meeting["id"]


def test_historical_vs_upcoming_meetings():
    """Test that historical and upcoming meetings are both present."""
    # Historical meetings (before Dec 2025)
    historical = [
        item for item in parsed_items
        if item["start"].year < 2025
        or (item["start"].year == 2025 and item["start"].month < 12)
    ]

    # Upcoming meetings (Dec 2025 or later)
    upcoming = [
        item for item in parsed_items
        if item["start"].year == 2025 and item["start"].month == 12
        or item["start"].year == 2026
    ]

    assert len(historical) == 13  # Historical meetings from 2016-2025
    assert len(upcoming) == 2     # Upcoming Council meetings (Regular + Special)
    assert len(historical) + len(upcoming) == 15


def test_meeting_titles_variety():
    """Test that various meeting title formats are captured."""
    titles = [item["title"] for item in parsed_items]

    # Check for various title formats that exist in our test data
    title_keywords = [
        "Regular Council Meeting",
        "Special Meeting",
        "Council",  # For committee meetings
    ]

    for keyword in title_keywords:
        assert any(keyword in title for title in titles), f"No meeting with '{keyword}' in title"


def test_years_coverage():
    """Test that meetings span multiple years."""
    years = set(item["start"].year for item in parsed_items)

    # Should have meetings from multiple years (2016-2026 in our test data)
    assert len(years) >= 8  # At least 8 different years
    assert 2016 in years
    assert 2025 in years or 2026 in years  # At least one recent/upcoming year
