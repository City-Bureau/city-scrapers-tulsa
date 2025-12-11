from datetime import datetime

from city_scrapers_core.constants import (
    CANCELLED,
    CLASSIFICATIONS,
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
        required_static_vars = ["agency", "name", "board_id", "location"]
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
    This class is designed to be used as a mixin for Tulsa city website.
    Agencies are identified by a board ID and a sub-committee ID.

    To use this mixin, create a child spider class that inherits from TulsaCityMixin
    and define the required static variables: agency, name, board_id, and location.
    """

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    name = None
    agency = None
    board_id = None
    location = None
    time_notes = None

    # Optional - most boards use "0" for main committee
    sub_committee_id = "0"

    timezone = "America/Chicago"
    base_url = "https://www.cityoftulsa.org"
    api_url = "https://www.cityoftulsa.org/umbraco/surface/AgendasByBoard/GetAgendasByBoard/"  # noqa

    def start_requests(self):
        """
        This spider mixin uses a POST request to fetch meeting
        data from the Tulsa meeting API using a board ID which
        is specified in each child spider class.
        """
        yield FormRequest(
            url=self.api_url,
            formdata={
                "boardID": str(self.board_id),
                "subCommitteeID": str(self.sub_committee_id),
            },
            callback=self.parse,
        )

    def parse(self, response):
        meetings_data = self.filter_meetings_data(response)

        for meeting_data in meetings_data:
            if "Annual" not in meeting_data.get("Meeting_Type", ""):
                meeting = self._parse_meeting(meeting_data)

                if meeting:
                    yield meeting

    def filter_meetings_data(self, response):
        """
        This function removes repeated instances of the same meeting
        on the same date and time. Some meetings appear multiple times
        in the API response, but with updated agenda information. In
        here, only the last instance of such meeting is kept.
        """
        try:
            data = response.json()
            meetings = []
            for meeting_data in data:
                date_str = meeting_data.get("Meeting_Date", "").strip()
                time_str = meeting_data.get("Meeting_Time", "").strip()

                date_time_str = date_str + " " + time_str if time_str else date_str

                if meetings and (
                    meetings[-1].get("Meeting_Date", "").strip()
                    + " "
                    + meetings[-1].get("Meeting_Time", "").strip()
                    == date_time_str
                ):
                    meetings[-1] = meeting_data
                else:
                    meetings.append(meeting_data)
            return meetings
        except Exception as e:
            self.logger.error(f"Failed to filter meetings data: {e}")
            return []

    def _parse_meeting(self, item):
        title = self._parse_title(item)
        start = self._parse_start(item)

        meeting = Meeting(
            title=title,
            description="",
            classification=self._parse_classification(title),
            start=start,
            end=None,
            all_day=False,
            time_notes=self.time_notes or "",
            location=self.location,
            links=self._parse_links(item),
            source=f"{self.base_url}/government/meeting-agendas/",
        )

        meeting["status"] = self._get_status(meeting, text=item.get("Meeting_Type", ""))
        meeting["id"] = self._get_id(meeting)

        return meeting

    def _parse_title(self, item):
        board_name = item.get("Board_Name", "")
        meeting_type = item.get("Meeting_Type", "")

        if meeting_type and meeting_type.lower() not in ["regular"]:
            return f"{board_name} - {meeting_type}"
        return board_name or self.agency

    def _parse_start(self, item):
        date_str = item.get("Meeting_Date", "")
        time_str = item.get("Meeting_Time", "")

        if not date_str:
            return None

        # Parse date (format: MM/DD/YYYY)
        date_obj = datetime.strptime(date_str.strip(), "%m/%d/%Y")

        # Parse time if available (format: H:MMAM/PM)
        if time_str:
            try:
                time_obj = datetime.strptime(time_str.strip(), "%I:%M%p")
                return date_obj.replace(hour=time_obj.hour, minute=time_obj.minute)
            except ValueError:
                pass

        return date_obj

    def _parse_classification(self, title):
        if not title:
            return NOT_CLASSIFIED

        sub_agencies = [sub_agency.strip().lower() for sub_agency in title.split("-")]

        for part in sub_agencies[1:2] + sub_agencies[0:1]:
            for classification in CLASSIFICATIONS:
                if classification.lower() in part:
                    return classification

        return NOT_CLASSIFIED

    def _parse_links(self, item):
        links = []
        agenda_id = item.get("Agenda_ID")
        if agenda_id:
            links.append(
                {
                    "href": (
                        f"{self.base_url}/apps/COTDisplayDocument/"
                        f"?DocumentType=Agenda&DocumentIdentifiers={agenda_id}"
                    ),
                    "title": "Agenda",
                }
            )

        return links

    def _get_status(self, item, text=""):
        if not text:
            return super()._get_status(item)

        text_lower = text.lower()

        # Check for cancellation indicators
        if any(word in text_lower for word in ["cancel", "reschedule", "postpone"]):
            return CANCELLED
        elif "special" in text_lower or "regular" in text_lower:
            if item.get("start") < datetime.now():
                return PASSED
            return TENTATIVE

        return super()._get_status(item)
