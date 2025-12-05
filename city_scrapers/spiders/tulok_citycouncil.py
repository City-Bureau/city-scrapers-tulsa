"""
Spider for Tulsa City Council meetings on Granicus platform.

This spider scrapes meeting data from the Granicus-based video archive page
for Tulsa City Council meetings.

URL: https://tulsa-ok.granicus.com/ViewPublisher.php?view_id=4
"""

import re
from datetime import datetime

from city_scrapers_core.constants import CITY_COUNCIL
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class TulsaGranicusCityCouncilSpider(CityScrapersSpider):
    name = "tulok_citycouncil"
    agency = "Tulsa City Council"
    timezone = "America/Chicago"
    start_urls = ["https://tulsa-ok.granicus.com/ViewPublisher.php?view_id=4"]

    # Override robots.txt - this is public meeting data
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def parse(self, response):
        """
        Parse the main Granicus page and extract City Council meetings.

        We target the CollapsiblePanel with ID "CollapsiblePanel20251" which contains
        the *City Council section.
        """
        # Find the City Council collapsible panel
        city_council_panel = response.css("div#CollapsiblePanel20251")

        if not city_council_panel:
            self.logger.warning("Could not find City Council panel on page")
            return

        # Extract all meeting rows from the table
        meeting_rows = city_council_panel.css("table.listingTable tbody tr.listingRow")

        self.logger.info(f"Found {len(meeting_rows)} City Council meetings")

        for row in meeting_rows:
            meeting = self._parse_meeting_row(row, response.url)
            if meeting:
                yield meeting

    def _parse_meeting_row(self, row, source_url):
        """
        Parse a single meeting row from the table.

        Args:
            row: Scrapy selector for a table row
            source_url: URL of the source page

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
            date_text = row.css('td.listItem[headers*="Date"]::text').getall()
            date_text = " ".join([t.strip() for t in date_text if t.strip()])

            start = self._parse_datetime(date_text)
            if not start:
                self.logger.warning(f"Could not parse date from: {date_text}")
                return None

            # Extract links (Agenda and Video)
            links = self._parse_links(row)

            # Build meeting item
            meeting = Meeting(
                title=title,
                description="",
                classification=CITY_COUNCIL,
                start=start,
                end=None,
                all_day=False,
                time_notes="",
                location={
                    "name": "City Hall",
                    "address": "175 E 2nd St, Tulsa, OK 74103",
                },
                links=links,
                source=source_url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            return meeting

        except Exception as e:
            self.logger.error(f"Error parsing meeting row: {e}")
            return None

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
            # Clean up the text - remove non-breaking spaces and extra whitespace
            date_text = re.sub(r"\s+", " ", date_text)
            date_text = date_text.replace("\xa0", " ")

            # Parse format: "Month Day, Year - HH:MM AM/PM"
            # Example: "November 19, 2025 - 5:00 PM"
            match = re.search(
                r"([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})\s*-\s*(\d{1,2}):(\d{2})\s*(AM|PM)",
                date_text,
            )

            if match:
                month_name, day, year, hour, minute, ampm = match.groups()

                # Build datetime string
                datetime_str = f"{month_name} {day}, {year} {hour}:{minute} {ampm}"

                # Parse the datetime
                dt = datetime.strptime(datetime_str, "%B %d, %Y %I:%M %p")
                return dt
            else:
                self.logger.warning(f"Could not match datetime pattern in: {date_text}")
                return None

        except Exception as e:
            self.logger.error(f"Error parsing datetime '{date_text}': {e}")
            return None

    def _parse_links(self, row):
        """
        Extract agenda and video links from the meeting row.

        Args:
            row: Scrapy selector for a table row

        Returns:
            List of link dictionaries
        """
        links = []

        # Extract Agenda link
        agenda_link = row.css('td.listItem a[href*="AgendaViewer"]::attr(href)').get()
        if agenda_link:
            # Ensure the link has the protocol
            if agenda_link.startswith("//"):
                agenda_link = "https:" + agenda_link
            links.append({"href": agenda_link, "title": "Agenda"})

        # Extract Video link from onclick attribute
        video_onclick = row.css(
            'td.listItem a[onclick*="MediaPlayer"]::attr(onclick)'
        ).get()
        if video_onclick:
            # Extract URL from window.open JS call
            match = re.search(r"window\.open\('([^']+)'", video_onclick)
            if match:
                video_link = match.group(1)
                if video_link.startswith("//"):
                    video_link = "https:" + video_link
                links.append({"href": video_link, "title": "Video"})

        return links
