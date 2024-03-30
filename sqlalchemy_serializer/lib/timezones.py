

def to_local_time(dt, tzinfo):
    normalized = dt.astimezone(tzinfo)
    return normalized.replace(tzinfo=None)


def format_dt(dt, tpl=None):
    if not tpl:
        return dt.isoformat()
    return dt.strftime(tpl)
