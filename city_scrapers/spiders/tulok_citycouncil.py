"""
Spider for Tulsa City Council meetings on Granicus platform.

This spider scrapes meeting data from the Granicus-based video archive page
for Tulsa City Council meetings.

URL: https://tulsa-ok.granicus.com/ViewPublisher.php?view_id=4
"""

import re
from datetime import datetime
from typing import Any, ClassVar

from city_scrapers_core.constants import CITY_COUNCIL
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class TulsaGranicusCityCouncilSpider(CityScrapersSpider):
    name = "tulok_citycouncil"
    agency = "Tulsa City Council"
    timezone = "America/Chicago"
    start_urls: ClassVar[list[str]] = [
        "https://tulsa-ok.granicus.com/ViewPublisher.php?view_id=4"
    ]
    location: ClassVar[dict[str, str]] = {
        "name": "City Hall",
        "address": "175 E 2nd St, Tulsa, OK 74103",
    }

    # Override robots.txt - this is public meeting data
    custom_settings: ClassVar[dict[str, Any]] = {
        "ROBOTSTXT_OBEY": False,
    }

    def parse(self, response):
        """
        Parse the main Granicus page and extract City Council meetings.

        We target CollapsiblePanels for *City Council sections across multiple years.
        Panel IDs follow the pattern: CollapsiblePanel2024X, CollapsiblePanel2023X, etc.
        where X is a digit (varies by year).
        """
        # Define panel IDs for each year (2016 through next year)
        # The panel ID pattern includes the year and a digit suffix
        # note: The "1" suffix is intentional and required. It specifically targets
        # City Council meetings (CollapsiblePanel{year}1) while excluding other
        # panels like committees (CollapsiblePanel{year}2, CollapsiblePanel{year}3, etc.).
        # Using a prefix selector would incorrectly match ALL panels for the year.
        year_panel_ids = {
            year: f"CollapsiblePanel{year}1"
            for year in range(2016, datetime.now().year + 2)
        }

        # Iterate through each year's panel
        for year, panel_id in year_panel_ids.items():
            city_council_panel = response.css(f"div#{panel_id}")

            if not city_council_panel:
                self.logger.info(f"Could not find City Council panel for {year} (ID: {panel_id})")
                continue

            # Extract all meeting rows from the table
            meeting_rows = city_council_panel.css("table.listingTable tbody tr.listingRow")

            if meeting_rows:
                self.logger.info(f"Found {len(meeting_rows)} City Council meetings for {year}")

                for row in meeting_rows:
                    meeting = self._parse_meeting_row(row, response)
                    if meeting:
                        yield meeting

        # Parse upcoming events section
        upcoming_meetings = self._parse_upcoming_events(response)
        for meeting in upcoming_meetings:
            yield meeting

    def _parse_meeting_row(self, row, response):
        """
        Parse a single meeting row from the table.

        Args:
            row: Scrapy selector for a table row
            response: Scrapy response object

        Returns:
            Meeting item or None
        """
        try:
            # Extract meeting title
            title = row.css('td.listItem[headers="Name"]::text').get()
            if title:
                title = title.strip()
            else:
                title = "City Council Meeting"

            # Extract date and time
            date_text = row.css('td.listItem[headers*="Date"]').xpath("normalize-space()").get()

            start = self._parse_datetime(date_text)
            if not start:
                self.logger.warning(f"Could not parse date from: {date_text}")
                return None

            # Extract links (Agenda and Video)
            links = self._parse_links(row, response)

            # Build meeting item
            meeting = Meeting(
                title=title,
                description="",
                classification=CITY_COUNCIL,
                start=start,
                end=None,
                all_day=False,
                time_notes="",
                location=self.location,
                links=links,
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

        except Exception:
            self.logger.exception("Error parsing meeting row")
            return None
        else:
            return meeting

    def _parse_datetime(self, date_text):
        """
        Parse datetime from the date cell text.

        Examples:
            "November 19, 2025 - 5:00 PM"
            "November  7, 2025 - 8:00 AM"

        Args:
            date_text: String containing date and time

        Returns:
            datetime object or None
        """
        if not date_text:
            return None

        try:
            # Parse format: "Month Day, Year - HH:MM AM/PM"
            # Example: "November 19, 2025 - 5:00 PM"
            match = re.search(
                r"([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})\s*-\s*(\d{1,2}):(\d{2})\s*([AaPp])\.?\s*[Mm]\.?",
                date_text,
            )

            if match:
                month_name, day, year, hour, minute, ampm_letter = match.groups()
                ampm = f"{ampm_letter.upper()}M"

                # Build datetime string
                datetime_str = f"{month_name} {day}, {year} {hour}:{minute} {ampm}"

                # Parse the datetime
                dt = datetime.strptime(datetime_str, "%B %d, %Y %I:%M %p")
                return dt
            else:
                self.logger.warning(f"Could not match datetime pattern in: {date_text}")
                return None

        except Exception:
            self.logger.exception("Error parsing datetime %r", date_text)
            return None

    def _parse_links(self, row, response):
        """
        Extract agenda and video links from the meeting row.

        Args:
            row: Scrapy selector for a table row
            response: Scrapy response object for URL joining

        Returns:
            List of link dictionaries
        """
        links = []

        # Extract Agenda link
        agenda_link = row.css('td.listItem a[href*="AgendaViewer"]::attr(href)').get()
        if agenda_link:
            links.append({"href": response.urljoin(agenda_link), "title": "Agenda"})

        # Extract Video link from onclick attribute
        video_onclick = row.css(
            'td.listItem a[onclick*="MediaPlayer"]::attr(onclick)'
        ).get()
        if video_onclick:
            # Extract URL from window.open JS call
            match = re.search(r'window\.open\(\s*[\'"]([^\'"]+)[\'"]', video_onclick)
            if match:
                video_link = match.group(1)
                links.append({"href": response.urljoin(video_link), "title": "Video"})

        return links

    def _parse_upcoming_events(self, response):
        """
        Parse upcoming events section and filter for Council meetings.

        Args:
            response: Scrapy response object

        Returns:
            List of Meeting items
        """
        meetings = []

        # Find the upcoming events table (summary attribute identifies it)
        upcoming_table = response.css('table.listingTable[summary*="Upcoming"]')

        if not upcoming_table:
            self.logger.info("Could not find upcoming events table")
            return meetings

        # Extract all meeting rows from the upcoming events table
        meeting_rows = upcoming_table.css("tbody tr.listingRow")

        council_count = 0
        for row in meeting_rows:
            # Extract meeting title to filter for Council meetings
            title = row.css('td.listItem[headers="Name"]::text').get()
            if title:
                title = title.strip()
                # Only process City Council meetings (not committee meetings)
                # Pattern: Must contain "Regular", "Special", or "Emergency"
                # AND must NOT contain "Committee"
                if re.search(r"^(Regular|Tulsa City Council|Council|City Council)?\s*(Council|Regular|Emergency Special|Special)?\s*Meeting\s*(Part\s*[\d])?", title, re.IGNORECASE) and not re.search(
                    r"\bcommittee\b", title, re.IGNORECASE
                ):
                    meeting = self._parse_upcoming_event_row(row, response)
                    if meeting:
                        meetings.append(meeting)
                        council_count += 1

        self.logger.info(f"Found {council_count} upcoming Council meetings")
        return meetings

    def _parse_upcoming_event_row(self, row, response):
        """
        Parse a single upcoming event row from the table.

        Args:
            row: Scrapy selector for a table row
            response: Scrapy response object

        Returns:
            Meeting item or None
        """
        try:
            # Extract meeting title
            title = row.css('td.listItem[headers="Name"]::text').get()
            if title:
                title = title.strip()
            else:
                title = "City Council Meeting"

            # Extract date and time from the Date column
            # This can contain either plain text date or "In Progress" with embedded link
            date_cell = row.css('td.listItem[headers="Date"]')

            # Get normalized text (automatically handles whitespace)
            date_text = date_cell.xpath("normalize-space()").get()

            # Skip "In Progress" text for date parsing
            if date_text:
                date_text = date_text.replace("In Progress", "").strip()

            # If no date found, check if this is an "In Progress" meeting
            # For "In Progress" meetings, we'll skip them as they don't have a future date
            if not date_text:
                # Check if the date cell contains "In Progress" link
                in_progress_link = date_cell.css('a[onclick*="MediaPlayer"]::text').get()
                if in_progress_link and "In Progress" in in_progress_link:
                    self.logger.info(f"Skipping 'In Progress' meeting: {title}")
                    return None

            start = self._parse_datetime(date_text)
            if not start:
                self.logger.warning(f"Could not parse date from upcoming event: {date_text}")
                return None

            # Extract links (Agenda and Video)
            links = self._parse_upcoming_event_links(row, response)

            # Build meeting item
            meeting = Meeting(
                title=title,
                description="",
                classification=CITY_COUNCIL,
                start=start,
                end=None,
                all_day=False,
                time_notes="",
                location=self.location,
                links=links,
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

        except Exception:
            self.logger.exception("Error parsing upcoming event row")
            return None
        else:
            return meeting

    def _parse_upcoming_event_links(self, row, response):
        """
        Extract agenda and video links from an upcoming event row.

        Args:
            row: Scrapy selector for a table row
            response: Scrapy response object for URL joining

        Returns:
            List of link dictionaries
        """
        links = []

        # Extract Agenda link (uses event_id instead of clip_id)
        agenda_link = row.css('td.listItem[headers="AgendaLink"] a[href*="AgendaViewer"]::attr(href)').get()
        if agenda_link:
            links.append({"href": response.urljoin(agenda_link), "title": "Agenda"})

        # Extract Video/Live link from either:
        # 1. ViewEventLink column (for live/in-progress meetings)
        # 2. Date column (for in-progress meetings with embedded link)

        # Check ViewEventLink column
        video_onclick = row.css('td.listItem[headers="ViewEventLink"] a[onclick*="MediaPlayer"]::attr(onclick)').get()

        # If not found, check Date column for in-progress meetings
        if not video_onclick:
            video_onclick = row.css('td.listItem[headers="Date"] a[onclick*="MediaPlayer"]::attr(onclick)').get()

        if video_onclick:
            # Extract URL from window.open JS call
            match = re.search(r'window\.open\(\s*[\'"]([^\'"]+)[\'"]', video_onclick)
            if match:
                video_link = match.group(1)
                links.append({"href": response.urljoin(video_link), "title": "Video"})

        return links
