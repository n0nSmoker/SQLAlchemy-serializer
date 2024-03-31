from datetime import datetime


def to_local_time(dt: datetime, tzinfo) -> datetime:
    normalized = dt.astimezone(tzinfo)
    return normalized.replace(tzinfo=None)


def format_dt(dt, tpl=None) -> str:
    if not tpl:
        return dt.isoformat()
    return dt.strftime(tpl)
