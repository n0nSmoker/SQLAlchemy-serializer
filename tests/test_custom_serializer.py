from .models import (CustomSerializerModel, DATETIME, TIME, DATE,
                     CUSTOM_TZINFO, CUSTOM_DATE_FORMAT, CUSTOM_TIME_FORMAT, CUSTOM_DATE_TIME_FORMAT)


def test_tzinfo_set_in_serializer(get_instance):
    """
    Checks how serializer applies tzinfo for datetime objects
    :param get_instance:
    :return:
    """
    i = get_instance(CustomSerializerModel)
    data = i.to_dict()

    # Check time/date formats
    assert 'date' in data
    assert data['date'] == DATE.strftime(CUSTOM_DATE_FORMAT)
    assert 'datetime' in data
    assert 'time' in data
    assert data['time'] == TIME.strftime(CUSTOM_TIME_FORMAT)

    # Timezone info affects only datetime objects
    assert data['datetime'] == DATETIME.astimezone(CUSTOM_TZINFO).strftime(CUSTOM_DATE_TIME_FORMAT)

    # Check other fields
    assert 'id' in data
    assert 'string' in data
    assert 'bool' in data

