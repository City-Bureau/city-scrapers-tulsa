from datetime import date, datetime

import scrapy
from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class TulokBoccSpider(CityScrapersSpider):
    name = "tulok_bocc"
    agency = "Tulsa Board of County Commissioners"
    timezone = "America/Chicago"
    api_base_url = "https://tulsacook.api.civicclerk.com"
    portal_base_url = "https://tulsacook.portal.civicclerk.com"
    category_filter = "categoryId+in+(26,40)"

    def start_requests(self):
        today = date.today()
        today_str = today.isoformat()
        year_start = f"{today.year}-01-01"
        urls = [
            # past events from year start up to today
            f"{self.api_base_url}/v1/Events?$filter=startDateTime+ge+{year_start}+and+startDateTime+lt+{today_str}+and+{self.category_filter}&$orderby=startDateTime+desc,+eventName+desc",  # noqa
            # upcoming events (today and future)
            f"{self.api_base_url}/v1/Events?$filter={self.category_filter}+and+startDateTime+ge+{today_str}&$orderby=startDateTime+asc,+eventName+asc",  # noqa
        ]
        for url in urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        data = response.json()
        events = data.get("value", [])

        for raw_event in events:
            meeting = Meeting(
                title=self._parse_title(raw_event),
                description=self._parse_description(raw_event),
                classification=self._parse_classification(raw_event),
                start=self._parse_start(raw_event),
                end=self._parse_end(raw_event),
                all_day=self._parse_all_day(raw_event),
                time_notes=self._parse_time_notes(raw_event),
                location=self._parse_location(raw_event),
                links=self._parse_links(raw_event),
                source=self._parse_source(response),
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

        # Handle pagination
        next_link = data.get("@odata.nextLink")
        if next_link:
            yield scrapy.Request(next_link, callback=self.parse)

    def _parse_title(self, raw_event):
        """Parse or generate meeting title."""
        return (
            raw_event.get("eventName")
            or raw_event.get("agendaName")
            or "Board of County Commissioners"
        )

    def _parse_description(self, raw_event):
        """Parse or generate meeting description."""
        return raw_event.get("eventDescription") or ""

    def _parse_classification(self, raw_event):
        """Parse or generate classification from allowed options."""
        return BOARD

    def _parse_start(self, raw_event):
        """Parse start datetime as a naive datetime object."""
        start_str = raw_event.get("startDateTime")
        return self._parse_dt(start_str)

    def _parse_end(self, raw_event):
        """Parse end datetime as a naive datetime object. Added by pipeline if None"""
        end_str = raw_event.get("endDateTime")
        return self._parse_dt(end_str)

    def _parse_time_notes(self, raw_event):
        """Parse any additional notes on the timing of the meeting"""
        return ""

    def _parse_all_day(self, raw_event):
        """Parse or generate all-day status. Defaults to False."""
        return False

    def _parse_location(self, raw_event):
        """Parse or generate location."""
        event_location = raw_event.get("eventLocation") or {}

        location_name = "Board of County Commissioners"
        address_parts = [
            event_location.get("address1") or "",
            event_location.get("address2") or "",
            ", ".join(
                part
                for part in [
                    event_location.get("city"),
                    event_location.get("state"),
                    event_location.get("zipCode"),
                ]
                if part
            ),
        ]
        address = " ".join(part for part in address_parts if part).strip()

        return {
            "name": location_name,
            "address": address,
        }

    def _parse_links(self, raw_event):
        """Parse or generate links."""
        event_id = raw_event.get("id")
        links = []
        for f in raw_event.get("publishedFiles", []):
            file_id = f.get("fileId")
            if not file_id or not event_id:
                continue
            links.append(
                {
                    "title": f.get("name") or f.get("type") or "Document",
                    "href": f"{self.portal_base_url}/event/{event_id}/files/agenda/{file_id}",
                }
            )
        return links

    def _parse_source(self, response):
        """Parse or generate source."""
        return response.url

    def _parse_dt(self, dt_str):
        """Parse an ISO datetime string into a naive datetime object."""
        if not dt_str:
            return None
        # Handle ISO format like '2025-11-19T11:30:00Z'
        dt_str = dt_str.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(dt_str)
            # Return naive datetime (strip timezone)
            return dt.replace(tzinfo=None)
        except ValueError:
            return None
