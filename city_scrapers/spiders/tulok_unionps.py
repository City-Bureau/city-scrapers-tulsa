import re
from datetime import datetime

import scrapy
from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class TulokUnionpsSpider(CityScrapersSpider):
    name = "tulok_unionps"
    agency = "Union Public Schools Board of Education"
    timezone = "America/Chicago"
    start_urls = [
        "https://www.unionps.org/about/board-of-education/agendas-and-minutes"
    ]

    meeting_location = {
        "name": "Union Public Schools Education Service Center",
        "address": "8506 E 61st St, Tulsa, OK 74133",
    }

    date_re = re.compile(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"  # noqa
        r"\s+([0-9lI]{1,2})(?:,?\s+)(\d{4})",
        flags=re.IGNORECASE,
    )

    def parse(self, response):
        """Start by fetching board page."""
        yield response.follow(
            "https://www.unionps.org/about/board-of-education",
            callback=self.parse_board_page,
            meta={"main_page": response},
        )

    def parse_board_page(self, response):
        """Parse description and prepare meetings."""
        main_page = response.meta["main_page"]

        p_html = response.css("#fsEl_21196 p").get()
        desc = p_html.split("<br")[0]
        desc = scrapy.Selector(text=desc).xpath("string()").get().strip()

        time_notes = (
            " ".join(
                t.strip().replace("\xa0", " ")
                for t in main_page.css("#fsEl_23341 p::text").getall()
                if t.strip()
            )
            or "Regular meetings typically begin at 7:00 PM"
        )

        seen_dates = set()
        sources = self._collect_sources(main_page)

        # Process each meeting
        for entry in sources:
            start_dt = self._parse_start_from_text(entry["text"])
            if not start_dt or start_dt.date() in seen_dates:
                continue
            seen_dates.add(start_dt.date())

            title = (
                self._parse_title(entry["anchor"])
                if entry["anchor"]
                else "Board of Education Meeting"
            )
            links = (
                self._collect_links(main_page, entry["anchor"])
                if entry["anchor"]
                else []
            )

            # If Board Report exists, fetch in parallel
            board_report_link = next(
                (l["href"] for l in links if l.get("title") == "Board Report"), None
            )
            if board_report_link:
                yield scrapy.Request(
                    url=board_report_link,
                    callback=self.parse_board_report,
                    errback=self.handle_board_report_error,
                    meta={
                        "meeting_data": {
                            "title": title,
                            "description": desc,
                            "start": start_dt,
                            "time_notes": time_notes,
                            "links": links,
                            "source_url": main_page.url,
                        }
                    },
                    dont_filter=True,
                )
            else:
                # No Board Report; yield immediately
                yield self._create_meeting(
                    title, desc, start_dt, time_notes, links, main_page.url
                )

    def _collect_sources(self, main_page):
        """Collect past and upcoming meeting sources."""
        sources = []
        # Past meetings
        for link in main_page.css("#fsEl_23352 section.fsPanel a"):
            file_name = (link.attrib.get("data-file-name") or "").lower()
            if "agenda" in file_name:
                sources.append(
                    {
                        "text": (link.xpath("string()").get() or "").strip(),
                        "anchor": link,
                    }
                )

        # Upcoming meetings
        for col in main_page.css("section#fsEl_23350 div.fsStyleColumn"):
            for text in col.xpath(".//p/text()").getall():
                for date_str in (s.strip() for s in text.split("\n") if s.strip()):
                    sources.append({"text": date_str, "anchor": None})
        return sources

    def parse_board_report(self, response):
        """Extract YouTube video from Board Report page."""
        data = response.meta["meeting_data"]

        if response.status != 404:
            youtube_link = self._extract_youtube_link(response)
            if youtube_link:
                data["links"].append({"href": youtube_link, "title": "Video"})

        yield self._create_meeting(
            data["title"],
            data["description"],
            data["start"],
            data["time_notes"],
            data["links"],
            data["source_url"],
        )

    def _extract_youtube_link(self, response):
        """Extract YouTube link from the 'Video' section specifically."""

        # Look for h3 with text "Video" and find iframe in following content
        video_section = response.xpath(
            '//h3[contains(text(), "Video")]/following-sibling::p//iframe[contains(@src, "youtube.com")]/@src'  # noqa
        ).get()
        if video_section:
            match = re.search(r"youtube\.com/embed/([a-zA-Z0-9_-]+)", video_section)
            if match:
                return f"https://www.youtube.com/watch?v={match.group(1)}"

        # Look for heading with "Video" and find YouTube link in following paragraph
        video_link = response.xpath(
            '//h3[contains(text(), "Video")]/following-sibling::p//a[contains(@href, "youtube.com/watch")]/@href'  # noqa
        ).get()
        if video_link:
            return video_link

        # Fallback - look for last iframe (Video section is usually last)
        iframe_src = response.css(
            'iframe[src*="youtube.com"]:last-of-type::attr(src)'
        ).get()
        if iframe_src:
            match = re.search(r"youtube\.com/embed/([a-zA-Z0-9_-]+)", iframe_src)
            if match:
                return f"https://www.youtube.com/watch?v={match.group(1)}"

        return None

    def handle_board_report_error(self, failure):
        """Yield meeting without video if Board Report fetch fails."""
        data = failure.request.meta["meeting_data"]
        yield self._create_meeting(
            data["title"],
            data["description"],
            data["start"],
            data["time_notes"],
            data["links"],
            data["source_url"],
        )

    def _create_meeting(
        self, title, description, start_dt, time_notes, links, source_url
    ):
        meeting = Meeting(
            title=title,
            description=description,
            classification=BOARD,
            start=start_dt,
            end=None,
            all_day=False,
            time_notes=time_notes,
            location=self.meeting_location,
            links=links,
            source=source_url,
        )
        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)
        return meeting

    def _parse_title(self, anchor):
        search_texts = [
            (anchor.attrib.get("data-file-name") or "").lower(),
            (anchor.xpath("string()").get() or "").lower(),
            (anchor.xpath("following-sibling::text()[1]").get() or "").lower(),
        ]
        return (
            "Board of Education Special Meeting"
            if any("special" in t for t in search_texts)
            else "Board of Education Meeting"
        )

    def _parse_start_from_text(self, text):
        """Parse a date from text, fixing common OCR typos."""
        m = self.date_re.search(text)
        if not m:
            return None
        month = m.group(1)
        day = int(m.group(2).replace("l", "1").replace("I", "1"))
        year = int(m.group(3))
        return datetime.strptime(f"{month} {day}, {year}", "%B %d, %Y").replace(
            hour=19, minute=0
        )

    def _collect_links(self, response, agenda_anchor):
        links = [
            {
                "href": response.urljoin(agenda_anchor.attrib.get("href") or ""),
                "title": "Agenda",
            }
        ]
        for link in agenda_anchor.xpath("following-sibling::a"):
            text = (link.xpath("string()").get() or "").strip()
            if self.date_re.search(text):
                break
            href = response.urljoin(link.attrib.get("href") or "")
            text_lower = text.lower()
            title_lower = (link.attrib.get("title") or "").lower()
            if "minutes" in text_lower or "minutes" in title_lower:
                links.append({"href": href, "title": "Minutes"})
            elif "board report" in text_lower or "board report" in title_lower:
                links.append({"href": href, "title": "Board Report"})
        return links
