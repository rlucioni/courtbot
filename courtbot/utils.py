import datetime

from courtbot import constants


def conversational_join(items, conjunction='and'):
    """
    Join the given items so they can be used in a sentence.

    Arguments:
        items (list): Items to join into a string.

    Keyword Arguments:
        conjunction (str): Conjunction to use when adding the last item to the
            joined list (e.g., and, or).

    Returns:
        str: The joined items.
    """
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f' {conjunction} '.join(items)
    else:
        all_but_last = ', '.join(items[:-1])
        last = items[-1]
        return f', {conjunction} '.join([all_but_last, last])


def hourly(minutes, tomorrow):
    """
    Convert raw availability data to an array of available hours.

    The scheduling API represent's a court's availability as follows:

    {
        'Id': 17,
        'Availability': [
            {
                'IsAvailable': False,
                'TimeId': 0,
            },
            {
                'IsAvailable': False,
                'TimeId': 1,
            },
            ...
            {
                'IsAvailable': False,
                'TimeId': 1439,
            }
        ]
    }

    Arguments:
        minutes (list): The 'Availability' list, an example of which is above.
        tomorrow (bool): Whether or not these times are for tomorrow.

    Returns:
        list: Hours during which the court is available.
    """
    hours = []
    now = datetime.datetime.now()

    for minute in minutes:
        if minute['TimeId'] in constants.TOP_OF_HOUR and minute['IsAvailable']:
            hour = minute['TimeId'] // 60

            if tomorrow or hour > now.hour:
                hours.append(hour)

    return hours


def slash_separated_date(tomorrow):
    """
    Build a slash-separated string representing today's or tomorrow's date.

    Arguments:
        tomorrow (bool): Whether or not to represent tomorrow's date.

    Returns:
        str: The slash-separated date.
    """
    day = datetime.datetime.now() + datetime.timedelta(days=1 if tomorrow else 0)

    return day.strftime('%m/%d/%Y')
