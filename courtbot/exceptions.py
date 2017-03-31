class CourtbotException(Exception):
    pass


class AvailabilityError(CourtbotException):
    pass


class BookingError(CourtbotException):
    pass
