import re
from datetime import datetime

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class TulokBoedSpider(CityScrapersSpider):
    name = "tulok_boed"
    agency = "Tulsa Public Schools Board of Education"
    timezone = "America/Chicago"
    start_urls = [
        "https://tulsaschools.diligent.community/Services/MeetingsService.svc/meetings?from=2024-12-01&to=9999-12-31"  # noqa
    ]
    agenda_url = "https://tulsaschools.diligent.community/Portal/MeetingInformation.aspx?Org=Cal&Id={}"  # noqa
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        """
        Parse meeting items from the Diligent Community API.
        Returns JSON array of meeting objects with full details.
        """
        data = response.json()
        for item in data:
            meeting = Meeting(
                title=item.get("MeetingTypeName") or "Board Meeting",
                description="",
                classification=BOARD,
                start=self._parse_start(item),
                end=None,
                all_day=False,
                time_notes="",
                location=self._parse_location(item),
                links=self._parse_links(item),
                source=self._parse_source(item),
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_start(self, item):
        """Parse start datetime from MeetingDateTime field.
        Format: '2025-06-16 18:30'
        """
        dt_str = item.get("MeetingDateTime")
        if dt_str:
            try:
                return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            except ValueError:
                return None
        return None

    def _parse_location(self, item):
        """Parse location from MeetingLocation field."""
        location_str = item.get("MeetingLocation", "")
        # Split on street address pattern (starts with number)
        match = re.search(r",\s*(\d+\s+.+)$", location_str)
        if match:
            name = location_str[: match.start()].strip()
            address = match.group(1)
        else:
            name = ""
            address = location_str
        return {"name": name, "address": address}

    def _parse_links(self, item):
        """Generate agenda link using meeting ID."""
        meeting_id = item.get("Id")
        if meeting_id:
            return [{"href": self.agenda_url.format(meeting_id), "title": "Agenda"}]
        return []

    def _parse_source(self, item):
        """Generate source link to meeting information page."""
        meeting_id = item.get("Id")
        if meeting_id:
            return self.agenda_url.format(meeting_id)
        return "https://tulsaschools.diligent.community/Portal/"
