# Tulsa Mixin Implementation Checklist

Step-by-step checklist for implementing the mixin pattern for Tulsa scrapers.

## Phase 1: Research & Discovery

- [ ] **Identify Tulsa's Calendar System**
  - [ ] Find the main meetings/calendar page
  - [ ] Document the URL pattern
  - [ ] Check if multiple agencies share the same system
  - [ ] Note any authentication requirements

- [ ] **Analyze URL Structure**
  - [ ] Document how agencies are identified (parameter, subdomain, path, etc.)
  - [ ] Example: `https://tulsa.gov/calendar?agency=XXX` or `https://tulsa.gov/XXX/calendar`
  - [ ] Note date filtering mechanisms
  - [ ] Document pagination (if any)

- [ ] **List Target Agencies**
  - [ ] City Council
  - [ ] Planning Commission
  - [ ] Parks Board
  - [ ] Zoning Board
  - [ ] Other boards/committees
  - [ ] Document their identifiers

## Phase 2: HTML Analysis

- [ ] **Calendar List Page**
  - [ ] Identify CSS selector for meeting items
  - [ ] Identify link to detail page
  - [ ] Note any agency-specific filtering
  - [ ] Check for JavaScript rendering (may need Playwright)

- [ ] **Meeting Detail Page**
  - [ ] Document title selector
  - [ ] Document description selector
  - [ ] Document date selector
  - [ ] Document time selector
  - [ ] Document location selectors (name, address components)
  - [ ] Document document links selector
  - [ ] Check for agenda/minutes availability

- [ ] **Test Selectors in Scrapy Shell**
  ```bash
  scrapy shell "URL_HERE"
  # Test each selector
  response.css("selector").getall()
  ```

## Phase 3: Update Mixin Code

### File: `city_scrapers/mixins/tulsa_city.py`

- [ ] **Update Base Configuration**
  - [ ] Set correct `base_url`
  - [ ] Set correct `timezone` (verify Tulsa's timezone)
  - [ ] Update default `links` array

- [ ] **Update `start_requests()` Method**
  - [ ] Adjust URL pattern to match Tulsa's structure
  - [ ] Verify date parameter format
  - [ ] Test date range logic

- [ ] **Update `parse()` Method**
  - [ ] Update selector for meeting items
  - [ ] Update selector for meeting links
  - [ ] Add any agency-specific filtering logic

- [ ] **Update `_parse_title()` Method**
  - [ ] Set correct CSS selector
  - [ ] Test with real page

- [ ] **Update `_parse_description()` Method**
  - [ ] Set correct CSS selector
  - [ ] Test text extraction
  - [ ] Test link extraction

- [ ] **Update `_parse_start()` Method**
  - [ ] Set correct date selector
  - [ ] Set correct time selector
  - [ ] Test time range parsing
  - [ ] Handle edge cases (TBD, cancelled, etc.)

- [ ] **Update `_parse_end()` Method**
  - [ ] Set correct selectors
  - [ ] Test end time extraction

- [ ] **Update `_parse_location()` Method**
  - [ ] Set correct name selector
  - [ ] Set correct address component selectors
  - [ ] Test address formatting

- [ ] **Update `_parse_links()` Method**
  - [ ] Set correct document links selector
  - [ ] Test URL resolution (relative vs absolute)
  - [ ] Test with pages that have no documents

## Phase 4: Configure Agencies

### File: `city_scrapers/spiders/tulsa_city.py`

- [ ] **Populate `spider_configs`**
  - [ ] Add configuration for each agency
  - [ ] Ensure unique `class_name` for each
  - [ ] Ensure unique `name` for each
  - [ ] Use descriptive `agency` names
  - [ ] Set correct `agency_id` for each

- [ ] **Verify Spider Creation**
  ```bash
  scrapy list
  # Should show all tulsa_city_* spiders
  ```

## Phase 5: Testing

- [ ] **Test Individual Spider**
  ```bash
  scrapy crawl tulsa_city_council
  ```
  - [ ] Verify it runs without errors
  - [ ] Check output for correctness
  - [ ] Verify all fields are populated

- [ ] **Test Multiple Agencies**
  - [ ] Run 2-3 different agency spiders
  - [ ] Verify each gets agency-specific data
  - [ ] Check for data leakage between agencies

- [ ] **Test Edge Cases**
  - [ ] Meetings with no end time
  - [ ] Meetings with no documents
  - [ ] Cancelled meetings
  - [ ] TBD locations
  - [ ] Special characters in titles

- [ ] **Validate Output**
  ```bash
  scrapy crawl tulsa_city_council -o output.json
  ```
  - [ ] Check JSON structure
  - [ ] Verify all required fields present
  - [ ] Verify datetime format
  - [ ] Verify URL format

## Phase 6: Add Unit Tests

- [ ] **Create Test Fixtures**
  - [ ] Save sample HTML responses
  - [ ] Create `tests/files/tulsa_city_list.html`
  - [ ] Create `tests/files/tulsa_city_detail.html`

- [ ] **Write Tests**
  - [ ] Test `_parse_title()`
  - [ ] Test `_parse_description()`
  - [ ] Test `_parse_start()`
  - [ ] Test `_parse_end()`
  - [ ] Test `_parse_location()`
  - [ ] Test `_parse_links()`
  - [ ] Test `_parse_classification()`

- [ ] **Run Tests**
  ```bash
  pytest tests/test_tulsa_city.py
  ```

## Phase 7: Documentation

- [ ] **Update README**
  - [ ] Document the mixin pattern
  - [ ] List all agency spiders
  - [ ] Add usage examples

- [ ] **Add Inline Comments**
  - [ ] Document any unusual logic
  - [ ] Explain agency-specific quirks
  - [ ] Note TODOs for future improvements

- [ ] **Create Agency List**
  - [ ] Document all agencies being scraped
  - [ ] Include URLs for reference
  - [ ] Note any special requirements

## Phase 8: Deployment

- [ ] **Run in Test Environment**
  - [ ] Verify all spiders run successfully
  - [ ] Check output quality
  - [ ] Monitor for errors

- [ ] **Set Up Scheduling**
  - [ ] Configure scraping frequency
  - [ ] Set up monitoring
  - [ ] Configure alerts for failures

- [ ] **Production Deploy**
  - [ ] Deploy code
  - [ ] Run initial scrape
  - [ ] Verify data in database

## Phase 9: Maintenance

- [ ] **Monitor for Changes**
  - [ ] Set up alerts for scraper failures
  - [ ] Periodically check website for changes
  - [ ] Update selectors as needed

- [ ] **Add New Agencies**
  - [ ] When new agencies are discovered
  - [ ] Just add to `spider_configs`
  - [ ] Test and deploy

## Common Issues Checklist

- [ ] **Spider Not Found**
  - [ ] Verified `create_spiders()` is called
  - [ ] Checked for import errors
  - [ ] Verified spider_configs syntax

- [ ] **Empty Results**
  - [ ] Tested selectors in scrapy shell
  - [ ] Checked if site uses JavaScript
  - [ ] Verified URL is correct

- [ ] **Wrong Agency Data**
  - [ ] Verified `agency_id` filtering works
  - [ ] Checked CSS selectors are agency-specific
  - [ ] Tested with multiple agencies

- [ ] **Datetime Parse Errors**
  - [ ] Verified date/time format
  - [ ] Checked for timezone info (should be naive)
  - [ ] Handled missing times

- [ ] **Missing Links**
  - [ ] Checked if documents exist on page
  - [ ] Verified selector matches HTML
  - [ ] Tested URL resolution

## Quick Commands Reference

```bash
# List all spiders
scrapy list | grep tulsa

# Test single spider
scrapy crawl tulsa_city_council

# Output to JSON
scrapy crawl tulsa_city_council -o output.json

# Output to CSV
scrapy crawl tulsa_city_council -o output.csv

# Test in shell
scrapy shell "https://tulsa.gov/calendar"

# Run with logging
scrapy crawl tulsa_city_council -L DEBUG

# Run all Tulsa spiders
scrapy list | grep tulsa | xargs -I {} scrapy crawl {}
```

## Completion Criteria

The implementation is complete when:

- [ ] All target agencies have spider configurations
- [ ] All spiders run without errors
- [ ] All required Meeting fields are populated
- [ ] Output validates against city_scrapers_core schema
- [ ] Unit tests pass
- [ ] Documentation is updated
- [ ] Code is deployed to production

## Resources

- [MIXIN_PATTERN_GUIDE.md](MIXIN_PATTERN_GUIDE.md) - Comprehensive guide
- [MIXIN_QUICK_REFERENCE.md](MIXIN_QUICK_REFERENCE.md) - Quick reference
- [Wichita Implementation](file:///Users/j/GitHub/city-scrapers-wichita)
- [city_scrapers_core](https://github.com/City-Bureau/city-scrapers-core)

## Notes

Use this section to track discoveries and decisions:

```
# Example notes:
- Tulsa uses calendar.aspx with CID parameter (similar to Wichita)
- Agency IDs found in HTML comments
- Some meetings have virtual locations: "Zoom - See link"
- Planning Commission uses different time format
```
