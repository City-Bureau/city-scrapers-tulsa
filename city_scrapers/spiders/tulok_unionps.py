import re
from datetime import datetime

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class TulokUnionpsSpider(CityScrapersSpider):
    name = "tulok_unionps"
    agency = "Union Public Schools Board of Education"
    timezone = "America/Chicago"
    start_urls = [
        "https://www.unionps.org/about/board-of-education/agendas-and-minutes"
    ]  # noqa

    meeting_location = {
        "name": "Union Public Schools Administration Building",
        "address": "8506 E 61st St, Tulsa, OK 74133",
    }

    date_re = re.compile(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"  # noqa
        r"\s+([0-9lI]{1,2})(?:,?\s+)(\d{4})",
        flags=re.IGNORECASE,
    )

    def parse(self, response):
        """Parse past and upcoming meetings in a single loop."""
        # Time notes
        time_notes_list = response.css("#fsEl_23341 p::text").getall()
        time_notes = " ".join(
            t.strip().replace("\xa0", " ") for t in time_notes_list if t.strip()
        )  # noqa
        if not time_notes:
            time_notes = "Regular meetings typically begin at 7:00 PM"

        seen_dates = set()

        # --- Combined sources: past panels + upcoming section ---
        sources = []

        # Past meetings with links
        panels = response.css("#fsEl_23352 section.fsPanel")
        for panel in panels:
            for link in panel.css("a"):
                text = (link.xpath("string()").get() or "").strip()
                file_attr = (link.attrib.get("data-file-name") or "").lower()
                if "agenda" not in file_attr:
                    continue
                sources.append({"text": text, "anchor": link})

        # Upcoming meetings without links
        upcoming_section = response.css("section#fsEl_23350")
        for col in upcoming_section.css("div.fsStyleColumn"):
            for text in col.xpath(".//p/text()").getall():
                for date_str in text.split("\n"):
                    date_str = date_str.strip()
                    if date_str:
                        sources.append({"text": date_str, "anchor": None})

        # --- Process all sources ---
        for entry in sources:
            start_dt = self._parse_start_from_text(entry["text"])
            if not start_dt or start_dt.date() in seen_dates:
                continue
            seen_dates.add(start_dt.date())

            if entry["anchor"]:
                links = self._collect_links(response, entry["anchor"])
                title = self._parse_title(entry["anchor"])
            else:
                links = []
                title = "Board of Education Meeting"

            meeting = Meeting(
                title=title,
                description="",
                classification=BOARD,
                start=start_dt,
                end=None,
                all_day=False,
                time_notes=time_notes,
                location=self.meeting_location,
                links=links,
                source=response.url,
            )
            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, anchor):
        """Determine if the meeting is Regular or Special."""
        search_texts = [
            (anchor.attrib.get("data-file-name") or "").lower(),
            (anchor.xpath("string()").get("") or "").lower(),
            (anchor.xpath("following-sibling::text()[1]").get("") or "").lower(),
        ]
        if any("special" in text for text in search_texts):
            return "Board of Education Special Meeting"
        return "Board of Education Meeting"

    def _parse_start_from_text(self, text):
        """Parse a date and return a datetime at 19:00 (7 PM), fixing common typos like 'l4' -> '14'."""  # noqa
        m = self.date_re.search(text)
        if not m:
            return None

        month = m.group(1)
        day_str = m.group(2).replace("l", "1").replace("I", "1")
        year = int(m.group(3))

        return datetime.strptime(
            f"{month} {int(day_str)}, {year}", "%B %d, %Y"
        ).replace(  # noqa
            hour=19, minute=0
        )

    def _collect_links(self, response, agenda_anchor):
        links = []
        # Agenda link (first link)
        href = response.urljoin(agenda_anchor.attrib.get("href") or "")
        links.append({"href": href, "title": "Agenda"})

        # Minutes and Board Reports, if any
        for link in agenda_anchor.xpath("following-sibling::a"):
            text = (link.xpath("string()").get() or "").strip()

            if self.date_re.search(text):
                break

            href = response.urljoin(link.attrib.get("href") or "")
            lt = text.lower()
            if "minutes" in lt:
                links.append({"href": href, "title": "Minutes"})
            elif "board report" in lt:
                links.append({"href": href, "title": "Board Report"})
        return links
