import pytz

from .models import FlatModel, DATETIME, TIME, DATE


def test_tzinfo_set_directly(get_instance):
    """
    Checks how serializer applies tzinfo for datetime objects
    :param get_instance:
    :return:
    """
    i = get_instance(FlatModel)

    # Default formats
    d_format = i.date_format
    dt_format = i.datetime_format
    t_format = i.time_format
    tzinfo = pytz.timezone('Europe/Moscow')

    data = i.to_dict(tzinfo=tzinfo)

    # No change for time and date objects
    assert 'date' in data
    assert data['date'] == DATE.strftime(d_format)
    assert 'datetime' in data
    assert 'time' in data
    assert data['time'] == TIME.strftime(t_format)

    # Timezone info affects only datetime objects
    assert data['datetime'] == DATETIME.astimezone(tzinfo).strftime(dt_format)

