from flask_babel import to_user_timezone, format_date, format_datetime


def to_local_time(t):
    return to_user_timezone(t).replace(tzinfo=None)

