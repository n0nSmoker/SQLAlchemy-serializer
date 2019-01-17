
def to_local_time(dt, tzinfo=None):
    if not tzinfo:
        return dt
    normalized = tzinfo.normalize(dt.astimezone(tzinfo))
    return normalized.replace(tzinfo=None)


def format_dt(dt, tpl):
    if not tpl:
        return dt.isoformat()
    return dt.strftime(tpl)



