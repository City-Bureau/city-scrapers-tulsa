from city_scrapers.mixins.tulsa_city import TulsaCityMixin

# Common location used by multiple agencies
default_location = {
    "name": "City Hall at One Technology Center",
    "address": "175 E 2nd St, Tulsa, OK 74103",
}

# Configuration for each spider
spider_configs = [
    {
        "class_name": "TulokAuditCommitteeSpider",
        "name": "tulok_audit_committee",
        "agency": "Audit Committee of the City of Tulsa",
        "board_id": "873",
        "location": {
            "name": "3rd Floor North Presentation Room, City Hall at One Technology Center",  # noqa
            "address": "175 E 2nd St, Tulsa, OK 74103",
        },
    },
    {
        "class_name": "TulokArtsCommissionSpider",
        "name": "tulok_arts_commission",
        "agency": "Arts Commission of City of Tulsa",
        "board_id": "882",
        "location": {
            "name": "3rd Floor North Presentation Room, City Hall at One Technology Center",  # noqa
            "address": "175 E 2nd St, Tulsa, OK 74103",
        },
    },
    {
        "class_name": "TulokAsianAffairsSpider",
        "name": "tulok_asian_affairs",
        "agency": "Asian Affairs Commission",
        "board_id": "1102",
        "location": {
            "name": "Check agenda for location details",
            "address": "Check agenda for location details",
        },
    },
    {
        "class_name": "TulokHispanicLatinxAffairsSpider",
        "name": "tulok_hispanic_latinx_affairs",
        "agency": "Greater Tulsa Area Hispanic/Latinx Affairs Commission",
        "board_id": "866",
        "location": default_location,
    },
    {
        "class_name": "TulokIndianAffairsSpider",
        "name": "tulok_indian_affairs",
        "agency": "Greater Tulsa Area Indian Affairs Commission",
        "board_id": "867",
        "location": default_location,
    },
    {
        "class_name": "TulokAfricanAmericanAffairsSpider",
        "name": "tulok_african_american_affairs",
        "agency": "Greater Tulsa Area African-American Affairs Commission",
        "board_id": "1085",
        "location": default_location,
    },
    {
        "class_name": "TulokBeyondApologySpider",
        "name": "tulok_beyond_apology",
        "agency": "Beyond Apology Commission",
        "board_id": "1103",
        "location": default_location,
    },
    {
        "class_name": "TulokPortAuthoritySpider",
        "name": "tulok_port_authority",
        "agency": "City of Tulsa-Rogers County Port Authority",
        "board_id": "860",
        "location": {
            "name": "Conference Room, Port Authority Offices",
            "address": "5350 Cimarron Rd, Catoosa, OK 74015",
        },
    },
    {
        "class_name": "TulokHousingAuthoritySpider",
        "name": "tulok_housing_authority",
        "agency": "Housing Authority of the City of Tulsa",
        "board_id": "869",
        "location": {
            "name": "Housing Authority Offices",
            "address": "415 East Independence, Tulsa, OK 74106",
        },
    },
    {
        "class_name": "TulokBoaSpider",
        "name": "tulok_boa",
        "agency": "Tulsa Board of Adjustment",
        "board_id": "858",
        "location": default_location,
    },
    {
        "class_name": "TulokCityCouncilSpider",
        "name": "tulok_city_council",
        "agency": "Tulsa City Council",
        "board_id": "899",
        "location": {
            "name": "4th Floor Room 411, One Technology Center",
            "address": "175 E 2nd St, Tulsa, OK 74103",
        },
    },
    {
        "class_name": "TulokCivilServiceSpider",
        "name": "tulok_civil_service",
        "agency": "Tulsa Civil Service Commission",
        "board_id": "861",
        "location": {
            "name": "10-South Conference Room, City Hall at One Technology Center",
            "address": "175 E 2nd St, Tulsa, OK 74103",
        },
    },
    {
        "class_name": "TulokCommunityDevSpider",
        "name": "tulok_community_dev",
        "agency": "Tulsa Community Development Committee",
        "board_id": "868",
        "location": {
            "name": "2nd Floor Council Chambers, City Hall at One Technology Center",
            "address": "175 E 2nd St, Tulsa, OK 74103",
        },
    },
    {
        "class_name": "TulokAppealsSpider",
        "name": "tulok_appeals",
        "agency": "Tulsa Board of Appeals",
        "board_id": "859",
        "location": {
            "name": "3rd Floor North Presentation Room, City Hall at One Technology Center",  # noqa
            "address": "175 E 2nd St, Tulsa, OK 74103",
        },
    },
    {
        "class_name": "TulokParksRecSpider",
        "name": "tulok_parks_rec",
        "agency": "Tulsa Parks and Recreation Board",
        "board_id": "877",
        "location": {
            "name": "Check agenda for location details",
            "address": "Check agenda for location details",
        },
    },
    {
        "class_name": "TulokStadiumTrustSpider",
        "name": "tulok_stadium_trust",
        "agency": "Tulsa Stadium Trust",
        "board_id": "897",
        "location": {
            "name": "Norlem Conference Center",
            "address": "201 North Elgin Avenue, Tulsa, OK 74120",
        },
    },
    {
        "class_name": "TulokWomensSpider",
        "name": "tulok_womens",
        "agency": "Tulsa Women's Commission",
        "board_id": "874",
        "location": {
            "name": "Room 411, City Hall at One Technology Center",
            "address": "175 E 2nd St, Tulsa, OK 74103",
        },
    },
]


def create_spiders():
    """
    Dynamically create spider classes using the spider_configs list
    and register them in the global namespace.
    """
    for config in spider_configs:
        class_name = config["class_name"]

        if class_name not in globals():
            # Build attributes dict without class_name to avoid duplication.
            # We make sure that the class_name is not already in the global namespace
            # Because some scrapy CLI commands like `scrapy list` will inadvertently
            # declare the spider class more than once otherwise
            attrs = {k: v for k, v in config.items() if k != "class_name"}

            # Dynamically create the spider class
            spider_class = type(
                class_name,
                (TulsaCityMixin,),
                attrs,
            )

            # Register the class in the global namespace using its class_name
            globals()[class_name] = spider_class


# Create all spider classes at module load
create_spiders()
