# City Scrapers Mixin Pattern Guide for Tulsa

This guide documents the mixin pattern used in city-scrapers projects for scrapers that share a common data source. Based on analysis of city-scrapers-wichita, city-scrapers-minn, and city-scrapers-det.

## Table of Contents
1. [Overview](#overview)
2. [Mixin Pattern Architecture](#mixin-pattern-architecture)
3. [Wichita City Pattern (Detailed Analysis)](#wichita-city-pattern-detailed-analysis)
4. [Spider Factory Pattern](#spider-factory-pattern)
5. [Meeting Item Structure](#meeting-item-structure)
6. [Adapting for Tulsa](#adapting-for-tulsa)
7. [Example Implementation](#example-implementation)

---

## Overview

The mixin pattern is used when multiple government agencies share a common data source (e.g., all boards/committees on a city's calendar system). Instead of creating separate spider classes with duplicated code, we:

1. Create a **mixin class** that handles all common scraping logic
2. Use a **metaclass** to enforce required static variables
3. Create a **spider factory** that dynamically generates spider classes with agency-specific configurations

### Benefits
- **DRY (Don't Repeat Yourself)**: Common logic in one place
- **Maintainability**: Fix bugs once, applies to all spiders
- **Scalability**: Easy to add new agencies
- **Type Safety**: Metaclass enforces required variables

---

## Mixin Pattern Architecture

### Three Key Components

#### 1. Metaclass (Enforcement Layer)
```python
class MixinMeta(type):
    """
    Metaclass that enforces the implementation of required static
    variables in child classes that inherit from the Mixin.
    """

    def __init__(cls, name, bases, dct):
        required_static_vars = ["agency", "name", "cid"]  # Define required vars
        missing_vars = [var for var in required_static_vars if var not in dct]

        if missing_vars:
            missing_vars_str = ", ".join(missing_vars)
            raise NotImplementedError(
                f"{name} must define the following static variable(s): {missing_vars_str}."
            )

        super().__init__(name, bases, dct)
```

**Purpose**: Validates at class creation time that all required variables are defined. Fails fast with clear error messages.

#### 2. Mixin Class (Logic Layer)
```python
class CityMixin(CityScrapersSpider, metaclass=MixinMeta):
    """
    Base mixin class that provides all common scraping logic.
    Child classes must define required static variables.
    """

    # Common configuration
    timezone = "America/Chicago"
    base_url = "https://city.gov"

    # Required to be overridden (enforced by metaclass)
    name = None
    agency = None
    cid = None  # Agency-specific identifier

    # Common methods
    def start_requests(self):
        """Generate initial requests"""
        pass

    def parse(self, response):
        """Parse listing page"""
        pass

    def _parse_detail(self, response):
        """Parse individual meeting page"""
        pass

    # Helper methods for parsing fields
    def _parse_title(self, item):
        pass

    def _parse_start(self, item):
        pass

    # ... more helper methods
```

#### 3. Spider Factory (Generation Layer)
```python
# Configuration for each spider
spider_configs = [
    {
        "class_name": "CityAgency1Spider",
        "name": "city_agency1",
        "agency": "City - Agency 1",
        "cid": "123",
    },
    {
        "class_name": "CityAgency2Spider",
        "name": "city_agency2",
        "agency": "City - Agency 2",
        "cid": "456",
    },
]

def create_spiders():
    """Dynamically create spider classes"""
    for config in spider_configs:
        class_name = config.pop("class_name")

        if class_name not in globals():
            spider_class = type(
                class_name,
                (CityMixin,),  # Base classes
                {**config},     # Attributes including name, agency, cid
            )
            globals()[class_name] = spider_class

create_spiders()
```

---

## Wichita City Pattern (Detailed Analysis)

### File: `/city_scrapers/mixins/wichita_city.py`

#### Metaclass Implementation
```python
class WichitaCityMixinMeta(type):
    def __init__(cls, name, bases, dct):
        required_static_vars = ["agency", "name", "cid"]
        missing_vars = [var for var in required_static_vars if var not in dct]

        if missing_vars:
            missing_vars_str = ", ".join(missing_vars)
            raise NotImplementedError(
                f"{name} must define the following static variable(s): {missing_vars_str}."
            )

        super().__init__(name, bases, dct)
```

**Required Variables:**
- `agency`: Full agency name (e.g., "Wichita City - Board of Park Commissioners")
- `name`: Spider name/slug (e.g., "wicks_city_bpc")
- `cid`: Agency identifier in URL (e.g., "28")

#### Mixin Class Structure

**Class Variables:**
```python
class WichitaCityMixin(CityScrapersSpider, metaclass=WichitaCityMixinMeta):
    # Enforced by metaclass (must be overridden)
    name = None
    agency = None
    cid = None

    # Common configuration
    timezone = "America/Chicago"
    base_url = "https://www.wichita.gov"
    links = [
        {
            "href": "https://www.wichita.gov/agendacenter",
            "title": "Wichita City, meeting materials page",
        }
    ]
```

**Core Methods:**

##### 1. `start_requests()` - Initial Request Generation
```python
def start_requests(self):
    """Generate request using an URL derived from base url,
    cid (agency identifier) and a range based on the date
    one month prior and six months ahead of the current date."""
    now = datetime.now()
    start_date = (now - relativedelta(months=1)).replace(day=1)
    start_date_str = start_date.strftime("%m/%d/%Y")
    end_date = (now + relativedelta(months=6)).replace(day=1)
    end_date_str = end_date.strftime("%m/%d/%Y")

    # Generate URL with cid parameter
    calendar_url = f"{self.base_url}/calendar.aspx?Keywords=&startDate={start_date_str}&enddate={end_date_str}&CID={self.cid}&showPastEvents=true"
    yield scrapy.Request(calendar_url, self.parse)
```

**Key Points:**
- Uses `self.cid` to filter to specific agency
- Date range: 1 month back, 6 months forward
- Single request yields all meetings for the agency

##### 2. `parse()` - List Page Parser
```python
def parse(self, response):
    """
    Parse the retrieved HTML, loop over the meeting, and parse the
    detail page for each one.
    """
    selector = f"#CID{self.cid} > ol > li"  # Agency-specific CSS selector
    for item in response.css(selector):
        event_query_string = item.css("h3 a::attr(href)").get()
        yield response.follow(event_query_string, self._parse_detail)
```

**Key Points:**
- Uses `self.cid` in CSS selector
- Follows links to detail pages
- Callback to `_parse_detail`

##### 3. `_parse_detail()` - Meeting Creation
```python
def _parse_detail(self, item):
    title = self._parse_title(item)
    meeting = Meeting(
        title=title,
        description=self._parse_description(item),
        classification=self._parse_classification(title),
        start=self._parse_start(item),
        end=self._parse_end(item),
        all_day=False,
        time_notes="",
        location=self._parse_location(item),
        links=self._parse_links(item),
        source=item.url,
    )

    meeting["status"] = self._get_status(meeting)
    meeting["id"] = self._get_id(meeting)

    yield meeting
```

**Key Points:**
- Creates `Meeting` item (from city_scrapers_core)
- Delegates field parsing to helper methods
- Uses inherited methods: `_get_status()`, `_get_id()`

##### 4. Field Parser Methods

**Title:**
```python
def _parse_title(self, item):
    """Extracts the event title."""
    return (
        item.css(
            "h2#ctl00_ctl00_MainContent_ModuleContent_ctl00_ctl04_eventTitle::text"
        )
        .get()
        .strip()
    )
```

**Description:**
```python
def _parse_description(self, item):
    """Extracts and cleans the HTML to return only text,
    including the original URLs in the text, while removing any
    hidden or non-printable characters."""
    description_sel = item.css("div[itemprop='description']")
    description_texts = []

    # Extract text nodes
    for text_node in description_sel.css("::text").getall():
        cleaned_text = re.sub(r"\s+", " ", text_node).strip()
        if cleaned_text:
            description_texts.append(cleaned_text)

    # Extract and format links
    for a_tag in description_sel.css("a"):
        text = a_tag.css("::text").get(default="").strip()
        href = a_tag.css("::attr(href)").get(default="").strip()
        if text and href:
            description_texts.append(f"{text}({href})")

    description = " ".join(description_texts).strip()
    description = re.sub(r"[^\x20-\x7E]+", "", description)
    return description
```

**Classification:**
```python
def _parse_classification(self, title):
    """Parse or generate classification from allowed options."""
    if not title:
        return NOT_CLASSIFIED
    elif "board" in title.lower():
        return BOARD
    elif "committee" in title.lower():
        return COMMITTEE
    elif "council" in title.lower():
        return CITY_COUNCIL
    else:
        return NOT_CLASSIFIED
```

**Start DateTime:**
```python
def _parse_start(self, response):
    """Extracts the start datetime as a naive datetime object.
    Some events have a dash in the time, indicating start and end times"""
    date_str = (
        response.css(
            "div#ctl00_ctl00_MainContent_ModuleContent_ctl00_ctl04_dateDiv::text"
        )
        .get()
        .strip()
    )
    time_sel = response.css(
        "div#ctl00_ctl00_MainContent_ModuleContent_ctl00_ctl04_time .specificDetailItem::text"
    ).get()
    has_dash = " - " in time_sel
    if has_dash:
        time_str = time_sel.strip().split(" - ")[0]
    else:
        time_str = time_sel.strip()
    datetime_str = f"{date_str} {time_str}"
    return parse(datetime_str)  # Returns naive datetime
```

**End DateTime:**
```python
def _parse_end(self, response):
    """Extracts the end datetime as a naive datetime object."""
    date_str = (
        response.css(
            "div#ctl00_ctl00_MainContent_ModuleContent_ctl00_ctl04_dateDiv::text"
        )
        .get()
        .strip()
    )
    time_sel = response.css(
        "div#ctl00_ctl00_MainContent_ModuleContent_ctl00_ctl04_time .specificDetailItem::text"
    ).get()
    has_dash = " - " in time_sel
    if has_dash:
        time_str = time_sel.strip().split(" - ")[1]
        datetime_str = f"{date_str} {time_str}"
        return parse(datetime_str)
    return None
```

**Location:**
```python
def _parse_location(self, item):
    """Extracts the event address and formats it"""
    name = (
        item.css(".specificDetailItem div[itemprop='name']::text")
        .get(default="")
        .strip()
    )
    street = (
        item.css(".specificDetailItem span[itemprop='streetAddress']::text")
        .get(default="")
        .strip()
    )
    locality = (
        item.css(".specificDetailItem span[itemprop='addressLocality']::text")
        .get(default="")
        .strip()
    )
    postal_code = (
        item.css(".specificDetailItem span[itemprop='postalCode']::text")
        .get(default="")
        .strip()
    )
    region = (
        item.css(".specificDetailItem span[itemprop='addressRegion']::text")
        .get(default="")
        .strip()
    )

    regionAndPostal = f"{region} {postal_code}"
    address_components = [street, locality, regionAndPostal]
    formatted_address = ", ".join(
        component for component in address_components if component
    )
    return {
        "name": name,
        "address": formatted_address,
    }
```

**Links:**
```python
def _parse_links(self, response):
    """Checks whether a "download agenda" link is present and
    any links are present in the "links" section."""

    new_links = self.links.copy()  # Copy the default links

    # Check "download agenda" button
    agenda_button = response.css("a.agendaDownload::attr(href)").get()
    if agenda_button:
        href = self.ensure_absolute_url(agenda_button)
        new_links.append({"href": href, "title": "Download agenda"})

    # Check for other links
    other_links = response.css(
        "#ctl00_ctl00_MainContent_ModuleContent_ctl00_ctl04_links a[itemprop='url']"
    )
    for link in other_links:
        href = self.ensure_absolute_url(link.css("::attr(href)").get())
        title = link.css("::text").get()
        new_links.append({"href": href, "title": title})

    return new_links

def ensure_absolute_url(self, url):
    """Check if a given URL is absolute or relative. If it's relative,
    return it as an absolute URL using the base_url."""
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        absolute_url = urljoin(self.base_url, url)
        return absolute_url
    else:
        return url
```

---

## Spider Factory Pattern

### File: `/city_scrapers/spiders/wicks_city.py`

#### Configuration List
```python
from city_scrapers.mixins.wichita_city import WichitaCityMixin

# Configuration for each spider
spider_configs = [
    {
        "class_name": "WicksCityERSBTSpider",
        "name": "wicks_city_ersbt",
        "agency": "Wichita City - Employees Retirement System Board of Trustees",
        "cid": "62",
    },
    {
        "class_name": "WicksCityMAPCSpider",
        "name": "wicks_city_mapc",
        "agency": "Wichita City - Metropolitan Area Planning Commission",
        "cid": "27",
    },
    # ... 42 total configurations
]
```

**Configuration Fields:**
- `class_name`: Python class name (PascalCase, must be unique)
- `name`: Spider slug (snake_case, used by Scrapy commands)
- `agency`: Full agency name (displayed in output)
- `cid`: Agency-specific ID used in URLs and CSS selectors

#### Dynamic Spider Creation
```python
def create_spiders():
    """
    Dynamically create spider classes using the spider_configs list
    and then register them in the global namespace. This approach
    is the equivalent of declaring each spider class in the same
    file but it is a little more concise.
    """
    for config in spider_configs:
        # Using config['class_name'] to dynamically define the class name
        class_name = config.pop("class_name")  # Remove to avoid conflicts

        # Check if already exists (prevents duplicate declarations)
        if class_name not in globals():
            spider_class = type(
                class_name,              # Class name
                (WichitaCityMixin,),     # Base classes tuple
                {**config},              # Class attributes dict
            )

            # Register the class in the global namespace
            globals()[class_name] = spider_class

# Call the function to create spiders
create_spiders()
```

**How It Works:**
1. `type()` is Python's dynamic class creation function
2. Signature: `type(name, bases, dict)`
   - `name`: String name of the class
   - `bases`: Tuple of base classes
   - `dict`: Dictionary of class attributes
3. `config.pop("class_name")` removes it from config dict
4. `{**config}` unpacks remaining config as class attributes
5. `globals()[class_name]` registers class so Scrapy can find it

**Equivalent Static Declaration:**
```python
# What the factory creates dynamically:
class WicksCityERSBTSpider(WichitaCityMixin):
    name = "wicks_city_ersbt"
    agency = "Wichita City - Employees Retirement System Board of Trustees"
    cid = "62"
```

#### Why Check `if class_name not in globals()`?

Some Scrapy CLI commands (like `scrapy list`) import the spider module multiple times. Without this check, the code would try to create the same class multiple times, causing errors.

---

## Meeting Item Structure

From `city_scrapers_core.items.Meeting`:

```python
from city_scrapers_core.items import Meeting

meeting = Meeting(
    title="Board Meeting",                    # Required: string
    description="Monthly board meeting",      # Optional: string
    classification=BOARD,                     # Required: from constants
    start=datetime(2024, 1, 15, 18, 0),      # Required: naive datetime
    end=datetime(2024, 1, 15, 19, 30),       # Optional: naive datetime or None
    all_day=False,                            # Required: boolean
    time_notes="",                            # Optional: string
    location={                                # Required: dict
        "name": "City Hall",
        "address": "123 Main St, City, ST 12345"
    },
    links=[                                   # Required: list of dicts
        {
            "href": "https://city.gov/agenda.pdf",
            "title": "Meeting Agenda"
        }
    ],
    source="https://city.gov/meeting/123"    # Required: string URL
)

# These are set by helper methods from CityScrapersSpider:
meeting["status"] = self._get_status(meeting)  # PASSED, TENTATIVE, CONFIRMED, CANCELLED
meeting["id"] = self._get_id(meeting)          # Generated from spider name + start datetime
```

### Field Specifications

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Meeting title |
| `description` | string | No | Meeting description |
| `classification` | string | Yes | One of: `BOARD`, `CITY_COUNCIL`, `COMMITTEE`, `NOT_CLASSIFIED` |
| `status` | string | Auto | One of: `PASSED`, `TENTATIVE`, `CONFIRMED`, `CANCELLED` |
| `start` | datetime | Yes | Naive datetime (no timezone) |
| `end` | datetime | No | Naive datetime or None |
| `all_day` | boolean | Yes | Whether meeting is all day |
| `time_notes` | string | No | Additional time information |
| `location` | dict | Yes | Must have `name` and `address` keys |
| `links` | list | Yes | List of dicts with `href` and `title` |
| `source` | string | Yes | URL of the meeting detail page |
| `id` | string | Auto | Generated by `_get_id()` method |

### Constants (from `city_scrapers_core.constants`)

```python
from city_scrapers_core.constants import (
    BOARD,           # For boards (e.g., "Board of Education")
    CITY_COUNCIL,    # For city council meetings
    COMMITTEE,       # For committees
    NOT_CLASSIFIED,  # When type is unclear

    PASSED,          # Meeting already occurred
    TENTATIVE,       # Meeting date/time not confirmed
    CONFIRMED,       # Meeting date/time confirmed
    CANCELLED,       # Meeting cancelled
)
```

---

## Adapting for Tulsa

### Step 1: Analyze Tulsa's Data Source

Before implementing, you need to:

1. **Identify the common platform/system**
   - Is there a shared calendar system URL?
   - What parameters identify different agencies?
   - Examples from other cities:
     - Wichita: `calendar.aspx?CID=XX`
     - Minneapolis: `GetCalenderList?committeeId=XX&meetingType=X`
     - Detroit: Multiple filter IDs

2. **Examine the HTML structure**
   - How are meetings listed?
   - What's the structure of detail pages?
   - Are there consistent CSS selectors?

3. **Document URL patterns**
   ```
   List page: https://tulsa.gov/calendar?agency=XXX&start=DATE&end=DATE
   Detail page: https://tulsa.gov/meeting/12345
   ```

### Step 2: Create the Mixin

**File: `/city_scrapers/mixins/tulsa_city.py`**

```python
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

import scrapy
from city_scrapers_core.constants import BOARD, CITY_COUNCIL, COMMITTEE, NOT_CLASSIFIED
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta


class TulsaCityMixinMeta(type):
    """
    Metaclass that enforces the implementation of required static
    variables in child classes that inherit from TulsaCityMixin.
    """

    def __init__(cls, name, bases, dct):
        required_static_vars = ["agency", "name", "agency_id"]
        missing_vars = [var for var in required_static_vars if var not in dct]

        if missing_vars:
            missing_vars_str = ", ".join(missing_vars)
            raise NotImplementedError(
                f"{name} must define the following static variable(s): {missing_vars_str}."
            )

        super().__init__(name, bases, dct)


class TulsaCityMixin(CityScrapersSpider, metaclass=TulsaCityMixinMeta):
    """
    This class is designed to scrape data from the City of Tulsa government website.
    Boards and committees are identified by a unique 'agency_id' value in the URL.

    To use this mixin, create a new spider class that inherits from this mixin.
    'agency', 'name', and 'agency_id' must be defined as static vars in the spider class.
    """

    # Required to be overridden (enforced by metaclass)
    name = None
    agency = None
    agency_id = None

    # Common configuration
    timezone = "America/Chicago"  # Tulsa is in Central Time
    base_url = "https://www.cityoftulsa.org"  # UPDATE WITH ACTUAL URL
    links = [
        {
            "href": "https://www.cityoftulsa.org/meetings",  # UPDATE
            "title": "Tulsa City, meeting materials page",
        }
    ]

    def start_requests(self):
        """
        Generate request using an URL derived from base url,
        agency_id (agency identifier) and a range based on the date
        one month prior and six months ahead of the current date.
        """
        now = datetime.now()
        start_date = (now - relativedelta(months=1)).replace(day=1)
        start_date_str = start_date.strftime("%m/%d/%Y")
        end_date = (now + relativedelta(months=6)).replace(day=1)
        end_date_str = end_date.strftime("%m/%d/%Y")

        # Generate URL - UPDATE THIS PATTERN BASED ON ACTUAL TULSA URL
        calendar_url = (
            f"{self.base_url}/calendar?"
            f"agency={self.agency_id}&"
            f"start={start_date_str}&"
            f"end={end_date_str}"
        )
        yield scrapy.Request(calendar_url, self.parse)

    def parse(self, response):
        """
        Parse the retrieved HTML, loop over the meetings, and parse the
        detail page for each one.
        """
        # UPDATE SELECTOR BASED ON ACTUAL HTML STRUCTURE
        selector = f".agency-{self.agency_id} .meeting-item"
        for item in response.css(selector):
            meeting_url = item.css("a.meeting-link::attr(href)").get()
            if meeting_url:
                yield response.follow(meeting_url, self._parse_detail)

    def _parse_detail(self, response):
        """Parse individual meeting detail page"""
        title = self._parse_title(response)
        meeting = Meeting(
            title=title,
            description=self._parse_description(response),
            classification=self._parse_classification(title),
            start=self._parse_start(response),
            end=self._parse_end(response),
            all_day=False,
            time_notes="",
            location=self._parse_location(response),
            links=self._parse_links(response),
            source=response.url,
        )

        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)

        yield meeting

    def _parse_title(self, response):
        """Extracts the event title."""
        # UPDATE SELECTOR BASED ON ACTUAL HTML
        return response.css("h1.meeting-title::text").get().strip()

    def _parse_description(self, response):
        """
        Extracts and cleans the HTML to return only text,
        including the original URLs in the text, while removing any
        hidden or non-printable characters.
        """
        # UPDATE SELECTOR BASED ON ACTUAL HTML
        description_sel = response.css("div.meeting-description")
        description_texts = []

        # Extract text nodes
        for text_node in description_sel.css("::text").getall():
            cleaned_text = re.sub(r"\s+", " ", text_node).strip()
            if cleaned_text:
                description_texts.append(cleaned_text)

        # Extract and format links
        for a_tag in description_sel.css("a"):
            text = a_tag.css("::text").get(default="").strip()
            href = a_tag.css("::attr(href)").get(default="").strip()
            if text and href:
                description_texts.append(f"{text}({href})")

        description = " ".join(description_texts).strip()
        description = re.sub(r"[^\x20-\x7E]+", "", description)
        return description

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if not title:
            return NOT_CLASSIFIED
        title_lower = title.lower()
        if "board" in title_lower:
            return BOARD
        elif "committee" in title_lower:
            return COMMITTEE
        elif "council" in title_lower:
            return CITY_COUNCIL
        else:
            return NOT_CLASSIFIED

    def _parse_start(self, response):
        """
        Extracts the start datetime as a naive datetime object.
        Some events have a dash in the time, indicating start and end times.
        """
        # UPDATE SELECTORS BASED ON ACTUAL HTML
        date_str = response.css(".meeting-date::text").get().strip()
        time_str = response.css(".meeting-time::text").get().strip()

        # Handle time ranges (e.g., "2:00 PM - 4:00 PM")
        if " - " in time_str:
            time_str = time_str.split(" - ")[0].strip()

        datetime_str = f"{date_str} {time_str}"
        return parse(datetime_str)

    def _parse_end(self, response):
        """Extracts the end datetime as a naive datetime object."""
        # UPDATE SELECTORS BASED ON ACTUAL HTML
        date_str = response.css(".meeting-date::text").get().strip()
        time_str = response.css(".meeting-time::text").get().strip()

        # Handle time ranges
        if " - " in time_str:
            end_time_str = time_str.split(" - ")[1].strip()
            datetime_str = f"{date_str} {end_time_str}"
            return parse(datetime_str)
        return None

    def _parse_location(self, response):
        """Extracts the event address and formats it"""
        # UPDATE SELECTORS BASED ON ACTUAL HTML
        name = response.css(".location-name::text").get(default="").strip()
        street = response.css(".location-street::text").get(default="").strip()
        city = response.css(".location-city::text").get(default="").strip()
        state = response.css(".location-state::text").get(default="").strip()
        zip_code = response.css(".location-zip::text").get(default="").strip()

        # Format the address
        address_parts = [street, city, f"{state} {zip_code}"]
        formatted_address = ", ".join(part for part in address_parts if part)

        return {
            "name": name,
            "address": formatted_address,
        }

    def _parse_links(self, response):
        """
        Checks whether an agenda link is present and any other
        document links are present in the links section.
        """
        new_links = self.links.copy()  # Copy the default links

        # UPDATE SELECTORS BASED ON ACTUAL HTML
        for link in response.css(".meeting-documents a"):
            href = link.css("::attr(href)").get()
            title = link.css("::text").get()
            if href and title:
                absolute_url = self.ensure_absolute_url(href)
                new_links.append({"href": absolute_url, "title": title.strip()})

        return new_links

    def ensure_absolute_url(self, url):
        """
        Check if a given URL is absolute or relative. If it's relative,
        return it as an absolute URL using the base_url.
        """
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            return urljoin(self.base_url, url)
        else:
            return url
```

### Step 3: Create the Spider Factory

**File: `/city_scrapers/spiders/tulsa_city.py`**

```python
from city_scrapers.mixins.tulsa_city import TulsaCityMixin

# Configuration for each spider
spider_configs = [
    {
        "class_name": "TulsaCityPlanningSpider",
        "name": "tulsa_city_planning",
        "agency": "Tulsa City - Planning Commission",
        "agency_id": "planning",  # UPDATE with actual ID
    },
    {
        "class_name": "TulsaCityCouncilSpider",
        "name": "tulsa_city_council",
        "agency": "Tulsa City Council",
        "agency_id": "council",  # UPDATE with actual ID
    },
    {
        "class_name": "TulsaCityParksBoardSpider",
        "name": "tulsa_city_parks",
        "agency": "Tulsa City - Parks Board",
        "agency_id": "parks",  # UPDATE with actual ID
    },
    # Add more agencies as needed
]


def create_spiders():
    """
    Dynamically create spider classes using the spider_configs list
    and then register them in the global namespace.
    """
    for config in spider_configs:
        class_name = config.pop("class_name")

        # Prevent duplicate class creation
        if class_name not in globals():
            spider_class = type(
                class_name,
                (TulsaCityMixin,),
                {**config},
            )
            globals()[class_name] = spider_class


# Call the function to create spiders
create_spiders()
```

### Step 4: Testing Individual Spiders

```bash
# List all spiders (should show all Tulsa agencies)
scrapy list

# Test a single spider
scrapy crawl tulsa_city_planning

# Test with output
scrapy crawl tulsa_city_planning -o output.json

# Test in interactive shell
scrapy shell "https://www.cityoftulsa.org/calendar?agency=planning"
```

### Step 5: Add New Agencies

Adding a new agency is as simple as adding a configuration:

```python
spider_configs = [
    # ... existing configs ...
    {
        "class_name": "TulsaCityZoningSpider",
        "name": "tulsa_city_zoning",
        "agency": "Tulsa City - Board of Zoning Appeals",
        "agency_id": "zoning",
    },
]
```

No need to write any new parsing code!

---

## Example Implementation

### Scenario: Tulsa Uses Same Platform as Wichita

If Tulsa uses the same calendar platform as Wichita (calendar.aspx with CID parameter):

**File: `/city_scrapers/mixins/tulsa_city.py`**
```python
# Just copy wichita_city.py and change:
# 1. Class names: WichitaCityMixin -> TulsaCityMixin
# 2. base_url: "https://www.wichita.gov" -> "https://www.cityoftulsa.org"
# 3. links array to point to Tulsa URLs
# 4. timezone if different (Tulsa is also Central Time)
```

**File: `/city_scrapers/spiders/tulsa_city.py`**
```python
from city_scrapers.mixins.tulsa_city import TulsaCityMixin

spider_configs = [
    {
        "class_name": "TulsaCityCouncilSpider",
        "name": "tulsa_city_council",
        "agency": "Tulsa City Council",
        "cid": "1",  # Find actual CID from Tulsa website
    },
    # Add more agencies...
]

def create_spiders():
    for config in spider_configs:
        class_name = config.pop("class_name")
        if class_name not in globals():
            spider_class = type(class_name, (TulsaCityMixin,), {**config})
            globals()[class_name] = spider_class

create_spiders()
```

### Scenario: Tulsa Uses Different Platform

If Tulsa uses a different platform, you'll need to:

1. **Analyze the URL structure and HTML**
2. **Update the mixin methods accordingly**
3. **Identify what makes each agency unique** (parameter, CSS class, etc.)

---

## Alternative Patterns from Other Cities

### Minneapolis Pattern (API-based)

**Key differences:**
- Uses JSON API instead of HTML scraping
- Requires Playwright for Cloudflare bypass
- Parameters: `committeeId` and `meetingType`

```python
class MinnCityMixin(CityScrapersSpider, metaclass=MinnCityMixinMeta):
    timezone = "America/North_Dakota/Beulah"
    base_url = "https://lims.minneapolismn.gov/Calendar/GetCalenderList"

    # Required variables
    committee_id = None
    meeting_type = None

    def start_requests(self):
        full_url = (
            f"{self.base_url}?"
            f"fromDate={self.from_date}&"
            f"toDate={self.to_date}&"
            f"meetingType={self.meeting_type}&"
            f"committeeId={self.committee_id}&"
            f"pageCount=1000&offsetStart=0"
        )
        yield scrapy.Request(
            url=full_url,
            meta={"playwright": True},  # For Cloudflare bypass
            callback=self.parse,
        )

    def parse(self, response):
        json_data = response.css("pre::text").get()
        data = json.loads(json_data)
        for item in data:
            meeting = Meeting(
                title=str(item["CommitteeName"]),
                description=str(item["Description"]),
                # ... more fields
            )
            yield meeting
```

**Usage:**
```python
spider_configs = [
    {
        "class_name": "MinnBoardSpider",
        "name": "minn_board",
        "agency": "Minneapolis City Council - Board",
        "committee_id": 16,
        "meeting_type": 1,
    },
]
```

### Detroit Pattern (Multi-source)

**Key differences:**
- Scrapes both events AND documents pages
- Multiple filter parameters
- Document matching by date

```python
class DetCityMixin:
    dept_cal_id = None   # Department filter for calendar
    dept_doc_id = None   # Department filter for documents
    agency_cal_id = None # Agency filter for calendar
    agency_doc_id = None # Agency filter for documents (can be list)

    def parse(self, response):
        if "Calendar-and-Events" in response.url:
            return self.parse_event_list(response)
        elif "/events/" in response.url:
            return self.parse_event_page(response)
        else:
            return self.parse_documents_page(response)
```

---

## Best Practices

### 1. Start with Manual Exploration
```bash
# Use scrapy shell to explore the website
scrapy shell "https://city.gov/calendar"

# Try different selectors
response.css("selector").getall()
response.xpath("//path").getall()
```

### 2. Handle Edge Cases
```python
def _parse_title(self, response):
    """Always include error handling"""
    title = response.css("h1::text").get()
    if not title:
        self.logger.warning(f"No title found for {response.url}")
        return "Untitled Meeting"
    return title.strip()
```

### 3. Use Descriptive Variable Names
```python
# Good
agency_id = "planning-commission"

# Bad
id = "pc"
```

### 4. Add Docstrings
```python
def _parse_location(self, response):
    """
    Extracts the event address and formats it.

    Returns:
        dict: Dictionary with 'name' and 'address' keys
    """
```

### 5. Log Important Information
```python
def parse(self, response):
    self.logger.info(f"Processing {len(items)} meetings for {self.agency}")
```

### 6. Test Thoroughly
```python
# Test with date ranges
# Test with different agencies
# Test with missing fields
# Test with malformed data
```

---

## Common Issues and Solutions

### Issue: Metaclass validation failing
**Error:** `NotImplementedError: SpiderName must define agency`

**Solution:** Ensure all required variables are defined:
```python
class MySpider(TulsaCityMixin):
    name = "my_spider"
    agency = "My Agency"
    agency_id = "123"  # Don't forget this!
```

### Issue: Spider not found by Scrapy
**Error:** `Spider not found: tulsa_city_planning`

**Solution:** Ensure `create_spiders()` is called at module level:
```python
# At the bottom of the file
create_spiders()  # Must be called!
```

### Issue: Duplicate spiders
**Error:** Multiple spiders with same name

**Solution:** Use the global check:
```python
if class_name not in globals():
    spider_class = type(...)
```

### Issue: CSS selectors not working
**Solution:** Use scrapy shell to test:
```bash
scrapy shell "URL"
>>> response.css("your-selector").getall()
```

---

## Next Steps for Tulsa

1. **Research Tulsa's website structure**
   - What calendar system does it use?
   - How are agencies identified?
   - What's the URL pattern?

2. **Create test spider**
   - Pick one agency
   - Write selectors for that agency
   - Test thoroughly

3. **Generalize to mixin**
   - Identify common patterns
   - Move to mixin class
   - Add metaclass validation

4. **Create spider factory**
   - List all agencies
   - Create configurations
   - Test each spider

5. **Add tests**
   - Write fixtures
   - Test parser methods
   - Test error cases

---

## References

- [Wichita Mixin](file:///Users/j/GitHub/city-scrapers-wichita/city_scrapers/mixins/wichita_city.py)
- [Wichita Factory](file:///Users/j/GitHub/city-scrapers-wichita/city_scrapers/spiders/wicks_city.py)
- [Minneapolis Mixin](file:///Users/j/GitHub/city-scrapers-minn/city_scrapers/mixins/minn_city.py)
- [Detroit Mixin](file:///Users/j/GitHub/city-scrapers-det/city_scrapers/mixins/det_city.py)
- [city_scrapers_core Documentation](https://github.com/City-Bureau/city-scrapers-core)

---

## Summary

The mixin pattern provides:
- **Code reuse**: Write parsing logic once
- **Maintainability**: Fix bugs in one place
- **Scalability**: Easy to add new agencies
- **Type safety**: Metaclass enforces requirements
- **Flexibility**: Override methods for special cases

Key files:
1. `/city_scrapers/mixins/tulsa_city.py` - Common logic
2. `/city_scrapers/spiders/tulsa_city.py` - Agency configurations

Next steps:
1. Analyze Tulsa's website
2. Adapt mixin to match structure
3. Add agency configurations
4. Test and deploy
