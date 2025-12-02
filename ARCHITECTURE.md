# Mixin Pattern Architecture

Visual guide to understanding the mixin pattern architecture.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    city_scrapers_core                            │
│  ┌──────────────────────┐      ┌───────────────────────────┐   │
│  │  CityScrapersSpider  │      │      Meeting Item         │   │
│  │  - _get_status()     │      │  - title                  │   │
│  │  - _get_id()         │      │  - start                  │   │
│  │  - Helper methods    │      │  - location               │   │
│  └──────────────────────┘      └───────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            ▲
                            │ inherits
                            │
┌─────────────────────────────────────────────────────────────────┐
│           city_scrapers/mixins/tulsa_city.py                     │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            TulsaCityMixinMeta (Metaclass)                 │  │
│  │  - Validates required variables at class creation time    │  │
│  │  - Enforces: name, agency, agency_id                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ▲                                      │
│                            │ uses as metaclass                    │
│                            │                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              TulsaCityMixin (Base Class)                  │  │
│  │                                                            │  │
│  │  Class Variables:                                         │  │
│  │  - timezone = "America/Chicago"                           │  │
│  │  - base_url = "https://cityoftulsa.org"                  │  │
│  │  - name = None (must be overridden)                       │  │
│  │  - agency = None (must be overridden)                     │  │
│  │  - agency_id = None (must be overridden)                  │  │
│  │                                                            │  │
│  │  Methods:                                                  │  │
│  │  - start_requests()      → Generate initial URLs          │  │
│  │  - parse()              → Parse list page                │  │
│  │  - _parse_detail()      → Parse detail page              │  │
│  │  - _parse_title()       → Extract title                  │  │
│  │  - _parse_description() → Extract description            │  │
│  │  - _parse_start()       → Extract start time             │  │
│  │  - _parse_end()         → Extract end time               │  │
│  │  - _parse_location()    → Extract location               │  │
│  │  - _parse_links()       → Extract document links         │  │
│  │  - _parse_classification() → Determine type              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            ▲
                            │ inherits
                            │
┌─────────────────────────────────────────────────────────────────┐
│          city_scrapers/spiders/tulsa_city.py                     │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              spider_configs (List)                        │  │
│  │                                                            │  │
│  │  [                                                         │  │
│  │    {                                                       │  │
│  │      "class_name": "TulsaCityCouncilSpider",             │  │
│  │      "name": "tulsa_city_council",                       │  │
│  │      "agency": "Tulsa City Council",                     │  │
│  │      "agency_id": "council"                              │  │
│  │    },                                                      │  │
│  │    {                                                       │  │
│  │      "class_name": "TulsaCityPlanningSpider",            │  │
│  │      "name": "tulsa_city_planning",                      │  │
│  │      "agency": "Tulsa City - Planning Commission",       │  │
│  │      "agency_id": "planning"                             │  │
│  │    },                                                      │  │
│  │    ...                                                     │  │
│  │  ]                                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                      │
│                            ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          create_spiders() Function                        │  │
│  │                                                            │  │
│  │  for config in spider_configs:                            │  │
│  │      class_name = config.pop("class_name")               │  │
│  │      if class_name not in globals():                      │  │
│  │          spider_class = type(                             │  │
│  │              class_name,                                  │  │
│  │              (TulsaCityMixin,),                          │  │
│  │              {**config}                                   │  │
│  │          )                                                 │  │
│  │          globals()[class_name] = spider_class            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                      │
│                            ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Dynamically Created Spider Classes                │  │
│  │                                                            │  │
│  │  class TulsaCityCouncilSpider(TulsaCityMixin):           │  │
│  │      name = "tulsa_city_council"                         │  │
│  │      agency = "Tulsa City Council"                       │  │
│  │      agency_id = "council"                               │  │
│  │                                                            │  │
│  │  class TulsaCityPlanningSpider(TulsaCityMixin):          │  │
│  │      name = "tulsa_city_planning"                        │  │
│  │      agency = "Tulsa City - Planning Commission"         │  │
│  │      agency_id = "planning"                              │  │
│  │                                                            │  │
│  │  ... (all other spiders)                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌──────────────┐
│   User runs  │
│ scrapy crawl │
│   spider     │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│              start_requests()                            │
│  - Builds URL with agency_id parameter                  │
│  - Adds date range filters                              │
│  URL: https://tulsa.gov/calendar?agency=council&...     │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│              parse(response)                             │
│  - Receives calendar list page                          │
│  - Finds meetings for this agency                       │
│  - Extracts links to detail pages                       │
└──────┬──────────────────────────────────────────────────┘
       │
       │ (for each meeting)
       ▼
┌─────────────────────────────────────────────────────────┐
│            _parse_detail(response)                       │
│  - Receives meeting detail page                         │
│  - Calls helper methods to extract fields               │
└──────┬──────────────────────────────────────────────────┘
       │
       ├─→ _parse_title()           → "City Council Meeting"
       ├─→ _parse_description()     → "Monthly meeting..."
       ├─→ _parse_classification()  → CITY_COUNCIL
       ├─→ _parse_start()           → datetime(2024, 1, 15, 18, 0)
       ├─→ _parse_end()             → datetime(2024, 1, 15, 19, 30)
       ├─→ _parse_location()        → {"name": "City Hall", "address": "..."}
       └─→ _parse_links()           → [{"href": "...", "title": "Agenda"}]
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│            Create Meeting Item                           │
│  meeting = Meeting(                                      │
│      title=...,                                          │
│      description=...,                                    │
│      classification=...,                                 │
│      start=...,                                          │
│      end=...,                                            │
│      location=...,                                       │
│      links=...,                                          │
│      source=response.url                                 │
│  )                                                       │
└──────┬──────────────────────────────────────────────────┘
       │
       ├─→ _get_status(meeting)  → "passed" / "tentative"
       └─→ _get_id(meeting)      → "tulsa_city_council/202401151800"
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│              yield meeting                               │
│  - Meeting goes to Scrapy pipeline                      │
│  - Validated, stored, exported                          │
└─────────────────────────────────────────────────────────┘
```

## Class Hierarchy

```
CityScrapersSpider (from city_scrapers_core)
    │
    ├─ Provides: _get_status(), _get_id()
    │
    └─→ TulsaCityMixin (mixins/tulsa_city.py)
           │
           ├─ Adds: All parsing logic
           ├─ Uses: Metaclass for validation
           │
           ├─→ TulsaCityCouncilSpider (dynamically created)
           │   ├─ name = "tulsa_city_council"
           │   ├─ agency = "Tulsa City Council"
           │   └─ agency_id = "council"
           │
           ├─→ TulsaCityPlanningSpider (dynamically created)
           │   ├─ name = "tulsa_city_planning"
           │   ├─ agency = "Tulsa City - Planning Commission"
           │   └─ agency_id = "planning"
           │
           └─→ ... (all other spiders)
```

## URL Structure Pattern

```
Base URL Structure:
https://www.cityoftulsa.org/calendar
    ↓
    ├─ ?agency=council          → City Council meetings
    ├─ ?agency=planning         → Planning Commission meetings
    ├─ ?agency=parks            → Parks Board meetings
    └─ ?agency=...              → Other agencies

Each agency's calendar:
https://www.cityoftulsa.org/calendar?agency=council&start=01/01/2024&end=06/30/2024
    ↓
    Returns list of meetings
    ↓
    <div class="meeting">
        <a href="/meeting/12345">Meeting Title</a>
    </div>
    ↓
    Follow to detail page
    ↓
https://www.cityoftulsa.org/meeting/12345
    ↓
    Extract all meeting data
```

## Agency Filtering Flow

```
Multiple Agencies Share Same Calendar System
    ↓
┌───────────────────────────────────────────────┐
│  Agency Filter Parameter: agency_id           │
│                                                │
│  council   → City Council                     │
│  planning  → Planning Commission              │
│  parks     → Parks Board                      │
│  zoning    → Zoning Board                     │
└───────────────────────────────────────────────┘
    ↓
Each Spider Has Unique agency_id
    ↓
┌───────────────────────────────────────────────┐
│  TulsaCityCouncilSpider                       │
│      agency_id = "council"                    │
│      ↓                                         │
│  URL: .../calendar?agency=council             │
│      ↓                                         │
│  Only gets City Council meetings              │
└───────────────────────────────────────────────┘

┌───────────────────────────────────────────────┐
│  TulsaCityPlanningSpider                      │
│      agency_id = "planning"                   │
│      ↓                                         │
│  URL: .../calendar?agency=planning            │
│      ↓                                         │
│  Only gets Planning Commission meetings       │
└───────────────────────────────────────────────┘
```

## Metaclass Validation Flow

```
Spider Class Creation
    ↓
┌─────────────────────────────────────────┐
│  TulsaCityMixinMeta.__init__()         │
│                                          │
│  Required variables:                    │
│  - name                                 │
│  - agency                               │
│  - agency_id                            │
└─────────────────────────────────────────┘
    ↓
    Check if all required vars are present
    ↓
┌────────────────┐     ┌──────────────────┐
│  All present?  │─NO─→│ Raise Error:     │
│                │     │ NotImplemented   │
└────────┬───────┘     └──────────────────┘
         │ YES
         ▼
┌─────────────────────────────────────────┐
│  Spider class created successfully      │
│  - Registered in globals()              │
│  - Available to Scrapy                  │
└─────────────────────────────────────────┘
```

## Comparison: With vs Without Mixin

### Without Mixin (Manual Approach)
```python
# 50+ lines per spider
class TulsaCityCouncilSpider(CityScrapersSpider):
    name = "tulsa_city_council"
    agency = "Tulsa City Council"

    def start_requests(self):
        # 10 lines of code
        pass

    def parse(self, response):
        # 10 lines of code
        pass

    def _parse_detail(self, response):
        # 30+ lines of code
        pass

    # ... all other methods

# Multiply by 20 agencies = 1000+ lines
# Bug fix requires changing 20 files
```

### With Mixin (Current Approach)
```python
# 1 mixin file with all logic (200 lines)
class TulsaCityMixin(CityScrapersSpider):
    # All common logic here

# 1 factory file with all configs (50 lines)
spider_configs = [
    {
        "class_name": "TulsaCityCouncilSpider",
        "name": "tulsa_city_council",
        "agency": "Tulsa City Council",
        "agency_id": "council",
    },
    # ... 19 more agencies (4 lines each)
]

# Total: 250 lines
# Bug fix requires changing 1 file
```

## Spider Lifecycle

```
1. Import Time
   ├─ Python imports tulsa_city.py
   ├─ create_spiders() function runs
   ├─ All spider classes created dynamically
   └─ Classes registered in globals()

2. Spider Discovery
   ├─ Scrapy lists available spiders
   └─ Finds all TulsaCity*Spider classes

3. Spider Execution
   ├─ User runs: scrapy crawl tulsa_city_council
   ├─ Scrapy instantiates TulsaCityCouncilSpider
   ├─ Spider inherits all methods from TulsaCityMixin
   └─ Uses council-specific agency_id

4. Data Collection
   ├─ start_requests() generates URLs
   ├─ parse() extracts meeting links
   ├─ _parse_detail() creates Meeting items
   └─ Meetings yielded to pipeline

5. Output
   ├─ Validated against schema
   ├─ Stored in database
   └─ Exported to JSON/CSV
```

## Key Design Principles

### 1. DRY (Don't Repeat Yourself)
```
Common logic → Mixin class
Agency-specific data → Configuration
Result: Minimal code duplication
```

### 2. Single Responsibility
```
Mixin: Handles scraping logic
Factory: Handles spider creation
Config: Defines agency parameters
```

### 3. Open/Closed Principle
```
Open for extension: Add new agencies via config
Closed for modification: Don't change mixin for new agencies
```

### 4. Fail Fast
```
Metaclass validates at import time
Invalid configuration = immediate error
No runtime surprises
```

### 5. Maintainability
```
Fix bug once in mixin
All spiders benefit immediately
No need to update multiple files
```

## Summary

The mixin pattern provides:

- **Code Reuse**: Write once, use many times
- **Type Safety**: Metaclass enforces requirements
- **Maintainability**: Single source of truth
- **Scalability**: Easy to add agencies
- **Consistency**: All spiders behave the same way

Key files to understand:
1. `mixins/tulsa_city.py` - The mixin class with all logic
2. `spiders/tulsa_city.py` - The factory that creates spiders
3. This architecture guide - How it all fits together
