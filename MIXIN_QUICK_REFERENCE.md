# Mixin Pattern Quick Reference

Quick reference for implementing the mixin pattern for Tulsa scrapers.

## File Structure

```
city_scrapers/
├── mixins/
│   └── tulsa_city.py          # Mixin class with all common logic
└── spiders/
    └── tulsa_city.py          # Spider factory with agency configs
```

## Minimal Implementation

### 1. Mixin Class (`mixins/tulsa_city.py`)

```python
from city_scrapers_core.constants import BOARD, CITY_COUNCIL, COMMITTEE, NOT_CLASSIFIED
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.parser import parse
import scrapy

class TulsaCityMixinMeta(type):
    def __init__(cls, name, bases, dct):
        required = ["agency", "name", "agency_id"]
        missing = [v for v in required if v not in dct]
        if missing:
            raise NotImplementedError(f"{name} must define: {', '.join(missing)}")
        super().__init__(name, bases, dct)

class TulsaCityMixin(CityScrapersSpider, metaclass=TulsaCityMixinMeta):
    name = None
    agency = None
    agency_id = None
    timezone = "America/Chicago"
    base_url = "https://www.cityoftulsa.org"

    def start_requests(self):
        url = f"{self.base_url}/calendar?agency={self.agency_id}"
        yield scrapy.Request(url, self.parse)

    def parse(self, response):
        for item in response.css(".meeting"):
            meeting_url = item.css("a::attr(href)").get()
            yield response.follow(meeting_url, self._parse_detail)

    def _parse_detail(self, response):
        meeting = Meeting(
            title=self._parse_title(response),
            description=self._parse_description(response),
            classification=self._parse_classification(response),
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
        return response.css("h1::text").get().strip()

    def _parse_description(self, response):
        return " ".join(response.css(".description::text").getall()).strip()

    def _parse_classification(self, response):
        title = response.css("h1::text").get("").lower()
        if "board" in title: return BOARD
        if "committee" in title: return COMMITTEE
        if "council" in title: return CITY_COUNCIL
        return NOT_CLASSIFIED

    def _parse_start(self, response):
        date_str = response.css(".date::text").get()
        time_str = response.css(".time::text").get()
        if " - " in time_str:
            time_str = time_str.split(" - ")[0]
        return parse(f"{date_str} {time_str}")

    def _parse_end(self, response):
        date_str = response.css(".date::text").get()
        time_str = response.css(".time::text").get()
        if " - " in time_str:
            return parse(f"{date_str} {time_str.split(' - ')[1]}")
        return None

    def _parse_location(self, response):
        return {
            "name": response.css(".location-name::text").get("").strip(),
            "address": response.css(".location-address::text").get("").strip(),
        }

    def _parse_links(self, response):
        links = []
        for link in response.css(".documents a"):
            links.append({
                "href": response.urljoin(link.css("::attr(href)").get()),
                "title": link.css("::text").get().strip(),
            })
        return links
```

### 2. Spider Factory (`spiders/tulsa_city.py`)

```python
from city_scrapers.mixins.tulsa_city import TulsaCityMixin

spider_configs = [
    {
        "class_name": "TulsaCityCouncilSpider",
        "name": "tulsa_city_council",
        "agency": "Tulsa City Council",
        "agency_id": "council",
    },
    {
        "class_name": "TulsaCityPlanningSpider",
        "name": "tulsa_city_planning",
        "agency": "Tulsa City - Planning Commission",
        "agency_id": "planning",
    },
]

def create_spiders():
    for config in spider_configs:
        class_name = config.pop("class_name")
        if class_name not in globals():
            spider_class = type(class_name, (TulsaCityMixin,), {**config})
            globals()[class_name] = spider_class

create_spiders()
```

## Usage

```bash
# List all spiders
scrapy list

# Run a spider
scrapy crawl tulsa_city_council

# Output to JSON
scrapy crawl tulsa_city_council -o output.json

# Test in shell
scrapy shell "https://www.cityoftulsa.org/calendar?agency=council"
```

## Adding New Agencies

Just add to `spider_configs`:

```python
{
    "class_name": "TulsaCityZoningSpider",
    "name": "tulsa_city_zoning",
    "agency": "Tulsa City - Board of Zoning Appeals",
    "agency_id": "zoning",
}
```

## Meeting Item Fields

```python
Meeting(
    title="Board Meeting",              # Required
    description="Meeting description",  # Optional
    classification=BOARD,                # Required (BOARD, COMMITTEE, CITY_COUNCIL, NOT_CLASSIFIED)
    start=datetime(2024, 1, 15, 18, 0), # Required (naive datetime)
    end=datetime(2024, 1, 15, 19, 30),  # Optional
    all_day=False,                       # Required
    time_notes="",                       # Optional
    location={                           # Required
        "name": "City Hall",
        "address": "123 Main St"
    },
    links=[                              # Required
        {"href": "url", "title": "Agenda"}
    ],
    source="https://..."                 # Required
)
```

## Common Selectors

Update these based on actual HTML:

```python
# List page
".meeting"                    # Meeting containers
"a.meeting-link::attr(href)" # Link to detail

# Detail page
"h1.title::text"             # Title
".description::text"         # Description
".date::text"                # Date
".time::text"                # Time
".location-name::text"       # Location name
".location-address::text"    # Address
".documents a"               # Document links
```

## Testing Individual Components

```python
# In scrapy shell
response.css("h1::text").get()
response.css(".description::text").getall()
response.css(".documents a::attr(href)").getall()
```

## Required Imports

```python
from city_scrapers_core.constants import BOARD, CITY_COUNCIL, COMMITTEE, NOT_CLASSIFIED
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from datetime import datetime
import scrapy
import re
```

## Key Points

1. **Metaclass enforces required variables** - Will fail at import if missing
2. **One mixin = many spiders** - All share same logic
3. **CSS selectors must match HTML** - Test in scrapy shell first
4. **Naive datetimes** - Don't include timezone in datetime objects
5. **Call create_spiders()** - Must be at module level
6. **Check globals()** - Prevents duplicate class creation
7. **Use response.urljoin()** - For relative URLs

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Spider not found | Ensure `create_spiders()` is called |
| Missing variable error | Add to spider config |
| CSS selector not working | Test in `scrapy shell` |
| Duplicate spider | Check `if class_name not in globals()` |
| Wrong timezone | Update `timezone` in mixin |
| Relative URLs | Use `response.urljoin(url)` |

## See Also

- [MIXIN_PATTERN_GUIDE.md](MIXIN_PATTERN_GUIDE.md) - Full detailed guide
- [Wichita Implementation](/Users/j/GitHub/city-scrapers-wichita/city_scrapers/mixins/wichita_city.py)
- [city_scrapers_core](https://github.com/City-Bureau/city-scrapers-core)
