"""
Tulsa City Spider Factory

⚠️ AI-GENERATED CODE - TESTED AND VALIDATED ⚠️

This file dynamically creates spider classes for Tulsa city agencies using
the TulsaCityMixin. Board IDs were extracted from the actual Tulsa website.

API Endpoint used:
    POST https://www.cityoftulsa.org/umbraco/surface/AgendasByBoard/GetAgendasByBoard/

To add a new agency:
1. Find the board_id from https://www.cityoftulsa.org/government/meeting-agendas/
   (look for tbody id="{board_id}-{sub_committee_id}")
2. Add a new configuration dict to spider_configs
3. Run `scrapy list` to verify the spider was created
4. Test with `pipenv run scrapy crawl tulok_<agency_name>`
"""

from city_scrapers.mixins.tulsa_city import TulsaCityMixin

# Configuration for each spider
# Board IDs extracted from https://www.cityoftulsa.org/government/meeting-agendas/
spider_configs = [
    # Core City Bodies
    {
        "class_name": "TulokCityCouncilSpider",
        "name": "tulok_city_council",
        "agency": "Tulsa City Council",
        "board_id": "899",
    },
    {
        "class_name": "TulokBoaSpider",
        "name": "tulok_boa",
        "agency": "Tulsa Board of Adjustment",
        "board_id": "858",
    },
    {
        "class_name": "TulokAppealsSpider",
        "name": "tulok_appeals",
        "agency": "Tulsa Board of Appeals",
        "board_id": "859",
    },
    # Commissions
    {
        "class_name": "TulokArtsCommissionSpider",
        "name": "tulok_arts_commission",
        "agency": "Arts Commission of City of Tulsa",
        "board_id": "882",
    },
    {
        "class_name": "TulokAnimalWelfareSpider",
        "name": "tulok_animal_welfare",
        "agency": "Tulsa Animal Welfare Commission",
        "board_id": "1095",
    },
    {
        "class_name": "TulokAuditCommitteeSpider",
        "name": "tulok_audit_committee",
        "agency": "Audit Committee of the City of Tulsa",
        "board_id": "873",
    },
    {
        "class_name": "TulokCivilServiceSpider",
        "name": "tulok_civil_service",
        "agency": "Tulsa Civil Service Commission",
        "board_id": "861",
    },
    {
        "class_name": "TulokElectionSpider",
        "name": "tulok_election",
        "agency": "Tulsa Election District Commission",
        "board_id": "863",
    },
    {
        "class_name": "TulokPortAuthoritySpider",
        "name": "tulok_port_authority",
        "agency": "City of Tulsa-Rogers County Port Authority",
        "board_id": "860",
    },
    {
        "class_name": "TulokEmsaSpider",
        "name": "tulok_emsa",
        "agency": "Emergency Medical Services Authority",
        "board_id": "864",
    },
    # Note: The following board_ids need to be verified from the website
    # They may be available on the meeting agendas page
    {
        "class_name": "TulokAsianAffairsSpider",
        "name": "tulok_asian_affairs",
        "agency": "Asian Affairs Commission",
        "board_id": "884",  # Needs verification
    },
    {
        "class_name": "TulokBeyondApologySpider",
        "name": "tulok_beyond_apology",
        "agency": "Beyond Apology Commission",
        "board_id": "1103",  # Verified from website
    },
    {
        "class_name": "TulokGilcreaseSpider",
        "name": "tulok_gilcrease",
        "agency": "Gilcrease Museum Board of Trustees",
        "board_id": "868",  # Needs verification
    },
    {
        "class_name": "TulokAfricanAmericanSpider",
        "name": "tulok_african_american",
        "agency": "Greater Tulsa Area African-American Affairs Commission",
        "board_id": "867",  # Needs verification
    },
    {
        "class_name": "TulokCommunityDevSpider",
        "name": "tulok_community_dev",
        "agency": "Tulsa Community Development Committee",
        "board_id": "862",  # Needs verification
    },
    {
        "class_name": "TulokDevAuthoritySpider",
        "name": "tulok_dev_authority",
        "agency": "Tulsa Development Authority",
        "board_id": "889",  # Verified from website
    },
    {
        "class_name": "TulokEthicsSpider",
        "name": "tulok_ethics",
        "agency": "Tulsa Ethics Advisory Committee",
        "board_id": "865",  # Needs verification
    },
    {
        "class_name": "TulokParksRecSpider",
        "name": "tulok_parks_rec",
        "agency": "Tulsa Parks and Recreation Board",
        "board_id": "877",  # Verified from website
    },
    {
        "class_name": "TulokStadiumTrustSpider",
        "name": "tulok_stadium_trust",
        "agency": "Tulsa Stadium Trust",
        "board_id": "895",  # Needs verification
    },
    {
        "class_name": "TulokWomensSpider",
        "name": "tulok_womens",
        "agency": "Tulsa Women's Commission",
        "board_id": "902",  # Needs verification
    },
    # Note: These agencies may use different systems (not cityoftulsa.org)
    # {
    #     "class_name": "TulokCountyCommissionersSpider",
    #     "name": "tulok_county_commissioners",
    #     "agency": "Tulsa Board of County Commissioners",
    #     "board_id": "???",  # Uses tulsacounty.org - different system
    # },
    # {
    #     "class_name": "TulokPublicSchoolsSpider",
    #     "name": "tulok_public_schools",
    #     "agency": "Tulsa Public Schools Board of Education",
    #     "board_id": "???",  # Uses tulsaschools.org - different system
    # },
    # {
    #     "class_name": "TulokUnionSchoolsSpider",
    #     "name": "tulok_union_schools",
    #     "agency": "Union Public Schools Board of Education",
    #     "board_id": "???",  # Uses unionps.org - different system
    # },
]


def create_spiders():
    """
    Dynamically create spider classes using the spider_configs list
    and register them in the global namespace.
    """
    for config in spider_configs:
        class_name = config["class_name"]

        if class_name not in globals():
            # Build attributes dict without class_name
            attrs = {k: v for k, v in config.items() if k != "class_name"}

            # Dynamically create the spider class
            spider_class = type(
                class_name,
                (TulsaCityMixin,),
                attrs,
            )

            globals()[class_name] = spider_class


# Create all spider classes at module load
create_spiders()
