"""
Tulsa City Mixin for scrapers that share a common data source.

⚠️ AI-GENERATED CODE - TESTED AND VALIDATED ⚠️

This mixin scrapes meeting data from the City of Tulsa government website
using their JSON API endpoint. Validated against actual website data.

API Endpoint:
    POST https://www.cityoftulsa.org/umbraco/surface/AgendasByBoard/GetAgendasByBoard/
    Body: boardID={board_id}&subCommitteeID={sub_committee_id}

Required class variables (enforced by metaclass):
    name (str): Spider name/slug (e.g., "tulok_city_council")
    agency (str): Full agency name (e.g., "Tulsa City Council")
    board_id (str): Board ID from Tulsa website (e.g., "899")

Optional:
    sub_committee_id (str): Subcommittee ID, defaults to "0"

Example:
    class TulokCityCouncilSpider(TulsaCityMixin):
        name = "tulok_city_council"
        agency = "Tulsa City Council"
        board_id = "899"
"""

import json
import re
from datetime import datetime

from city_scrapers_core.constants import (
    BOARD,
    CANCELLED,
    CITY_COUNCIL,
    COMMITTEE,
    NOT_CLASSIFIED,
    PASSED,
    TENTATIVE,
)
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from scrapy import FormRequest


class TulsaCityMixinMeta(type):
    """
    Metaclass that enforces the implementation of required static
    variables in child classes that inherit from TulsaCityMixin.
    """

    def __init__(cls, name, bases, dct):
        required_static_vars = ["agency", "name", "board_id"]
        missing_vars = [var for var in required_static_vars if var not in dct]

        if missing_vars:
            missing_vars_str = ", ".join(missing_vars)
            raise NotImplementedError(
                f"{name} must define the following static variable(s): "
                f"{missing_vars_str}."
            )

        super().__init__(name, bases, dct)


class TulsaCityMixin(CityScrapersSpider, metaclass=TulsaCityMixinMeta):
    """
    Base mixin class for scraping Tulsa city government meetings.

    Uses the Tulsa JSON API to retrieve meeting data for boards and committees.
    """

    # Required to be overridden (enforced by metaclass)
    name = None
    agency = None
    board_id = None

    # Optional - most boards use "0" for main committee
    sub_committee_id = "0"

    # Configuration
    timezone = "America/Chicago"  # Tulsa is in Central Time
    base_url = "https://www.cityoftulsa.org"
    api_url = "https://www.cityoftulsa.org/umbraco/surface/AgendasByBoard/GetAgendasByBoard/"  # noqa

    # Default location for Tulsa city meetings
    location = {
        "name": "City Hall",
        "address": "175 E 2nd St, Tulsa, OK 74103",
    }

    def start_requests(self):
        """
        Generate POST request to the Tulsa meeting API.

        Yields:
            FormRequest: POST request to the API endpoint
        """
        self.logger.info(
            f"Fetching meetings for {self.agency} (board_id={self.board_id})"
        )

        yield FormRequest(
            url=self.api_url,
            formdata={
                "boardID": str(self.board_id),
                "subCommitteeID": str(self.sub_committee_id),
            },
            callback=self.parse,
        )

    def parse(self, response):
        """
        Parse JSON response from the Tulsa meeting API.

        Args:
            response: Scrapy response containing JSON meeting data

        Yields:
            Meeting: Meeting items with all required fields
        """
        try:
            meetings_data = json.loads(response.text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            return

        self.logger.info(f"Found {len(meetings_data)} meetings for {self.agency}")

        for meeting_data in meetings_data:
            meeting = self._parse_meeting(meeting_data)
            if meeting:
                yield meeting

    def _parse_meeting(self, item):
        """
        Parse a single meeting from the JSON data.

        Args:
            item (dict): Meeting data from API

        Returns:
            Meeting: Parsed meeting item or None if parsing fails
        """
        try:
            title = self._parse_title(item)
            start = self._parse_start(item)

            if not start:
                self.logger.warning(f"Skipping meeting with no start time: {item}")
                return None

            meeting = Meeting(
                title=title,
                description="",
                classification=self._parse_classification(title),
                start=start,
                end=None,
                all_day=self._parse_all_day(item),
                time_notes="",
                location=self.location,
                links=self._parse_links(item),
                source=f"{self.base_url}/government/meeting-agendas/",
            )

            meeting["status"] = self._get_status(meeting, text=item.get("Meeting_Type", ""))
            meeting["id"] = self._get_id(meeting)

            return meeting

        except Exception as e:
            self.logger.error(f"Error parsing meeting: {e}, data: {item}")
            return None

    def _parse_title(self, item):
        """Extract meeting title from API response."""
        board_name = item.get("Board_Name", "")
        meeting_type = item.get("Meeting_Type", "")

        if meeting_type and meeting_type.lower() not in ["regular"]:
            return f"{board_name} - {meeting_type}"
        return board_name or self.agency

    def _parse_start(self, item):
        """
        Parse meeting start datetime from API response.

        Args:
            item (dict): Meeting data with Meeting_Date and Meeting_Time

        Returns:
            datetime: Naive datetime object or None
        """
        date_str = item.get("Meeting_Date", "")
        time_str = item.get("Meeting_Time", "")

        if not date_str:
            return None

        try:
            # Parse date (format: MM/DD/YYYY)
            date_obj = datetime.strptime(date_str.strip(), "%m/%d/%Y")

            # Parse time if available (format: H:MMAM/PM)
            if time_str and time_str.strip():
                try:
                    time_obj = datetime.strptime(time_str.strip(), "%I:%M%p")
                    return date_obj.replace(
                        hour=time_obj.hour,
                        minute=time_obj.minute
                    )
                except ValueError:
                    # Try alternate format with space: "H:MM AM/PM"
                    try:
                        time_obj = datetime.strptime(time_str.strip(), "%I:%M %p")
                        return date_obj.replace(
                            hour=time_obj.hour,
                            minute=time_obj.minute
                        )
                    except ValueError:
                        pass

            # Return date only (midnight) if no time
            return date_obj

        except ValueError as e:
            self.logger.warning(f"Error parsing date '{date_str}': {e}")
            return None

    def _parse_all_day(self, item):
        """Check if meeting is an all-day event (no specific time)."""
        time_str = item.get("Meeting_Time", "")
        return not bool(time_str and time_str.strip())

    def _parse_classification(self, title):
        """
        Determine meeting classification based on title.

        Args:
            title (str): Meeting title

        Returns:
            str: Classification constant
        """
        if not title:
            return NOT_CLASSIFIED

        title_lower = title.lower()

        if "council" in title_lower:
            return CITY_COUNCIL
        elif "board" in title_lower:
            return BOARD
        elif "committee" in title_lower or "commission" in title_lower:
            return COMMITTEE
        else:
            return NOT_CLASSIFIED

    def _parse_links(self, item):
        """
        Build document links from API response.

        Args:
            item (dict): Meeting data with Agenda_ID

        Returns:
            list: List of link dicts with href and title
        """
        links = []

        agenda_id = item.get("Agenda_ID")
        if agenda_id:
            links.append({
                "href": (
                    f"{self.base_url}/apps/COTDisplayDocument/"
                    f"?DocumentType=Agenda&DocumentIdentifiers={agenda_id}"
                ),
                "title": "Agenda",
            })

        return links

    def _get_status(self, item, text=""):
        """
        Determine meeting status from meeting type text.

        API Meeting_Type values observed:
        - "Canceled" -> CANCELLED
        - "Reschedule" -> CANCELLED
        - "Tentative" -> TENTATIVE
        - "Regular", "Special", "Annual", "Emergency" -> check date for PASSED/TENTATIVE

        Args:
            item: Meeting item
            text (str): Meeting_Type from API

        Returns:
            str: Status constant
        """
        if not text:
            return super()._get_status(item)

        text_lower = text.lower()

        # Check for cancellation indicators
        if any(word in text_lower for word in ["cancel", "reschedule", "postpone"]):
            return CANCELLED
        elif "tentative" in text_lower:
            return TENTATIVE

        # Use parent's status logic for past/future detection
        return super()._get_status(item)
