import datetime


# Each court has a resource ID. Z-Center courts 1-5 have resource IDs 17-21.
COURTS = {
    court_number: resource_id for court_number, resource_id in zip(range(1, 6), range(17, 22))
}

RESOURCES = {
    resource_id: court_number for court_number, resource_id in COURTS.items()
}

HOURS = {
    hour: datetime.datetime.now().replace(hour=hour).strftime('%-I %p') for hour in range(24)
}

# Minutes elapsed at the top of each hour.
TOP_OF_HOUR = {hour * 60 for hour in HOURS.keys()}
