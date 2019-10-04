from .models import FlatModel, DATETIME, TIME, DATE, MONEY


def test_no_defaults_no_rules(get_instance):
    """
    Checks to_dict method of flat model with no predefined options
    :param get_instance:
    :return:
    """
    i = get_instance(FlatModel)
    data = i.to_dict()

    # Check SQLAlchemy fields
    assert 'id' in data
    assert 'string' in data
    assert data['string'] == i.string
    assert 'date' in data
    assert 'time' in data
    assert 'datetime' in data
    assert 'bool' in data
    assert data['bool'] == i.bool
    assert 'null' in data
    assert data['null'] is None

    # Check non-sql fields (not included in this case, need to be defined explicitly)
    assert 'list' not in data
    assert 'set' not in data
    assert 'dict' not in data
    assert 'prop' not in data
    assert 'method' not in data
    assert '_protected_method' not in data
    assert 'money' not in data


def test_default_formats(get_instance):
    """
    Check date/datetime/time/decimal default formats in resulting JSON of flat model with no predefined options
    :param get_instance:
    :return:
    """
    i = get_instance(FlatModel)

    # Default formats
    d_format = i.date_format
    dt_format = i.datetime_format
    t_format = i.time_format
    decimal_format = i.decimal_format

    # Include non-SQL field to check decimal_format and bytes
    data = i.to_dict(rules=('money', 'prop_with_bytes'))

    assert 'date' in data
    assert data['date'] == DATE.strftime(d_format)
    assert 'datetime' in data
    assert data['datetime'] == DATETIME.strftime(dt_format)
    assert 'time' in data
    assert data['time'] == TIME.strftime(t_format)

    assert 'money' in data
    assert data['money'] == decimal_format.format(MONEY)

    assert 'prop_with_bytes' in data
    assert data['prop_with_bytes'] == i.prop_with_bytes.decode()


def test_formats_got_in_runtime(get_instance):
    """
    Check date/datetime/time/decimal default formats in resulting JSON passed as the parameters of to_dict func
    :param get_instance:
    :return:
    """
    d_format = '%Y/%m/%d'
    dt_format = '%Y/%m/%d %H:%M'
    t_format = '>%H<'
    decimal_format = '{:.3}'

    i = get_instance(FlatModel)

    # Check that default formats are different
    assert d_format != i.date_format
    assert dt_format != i.datetime_format
    assert t_format != i.time_format
    assert decimal_format != i.decimal_format

    data = i.to_dict(
        date_format=d_format,
        datetime_format=dt_format,
        time_format=t_format,
        decimal_format=decimal_format,
        rules=('money',)  # Include non-SQL field to check decimal_format
    )

    # Check serialized formats
    assert 'date' in data
    assert data['date'] == DATE.strftime(d_format)
    assert 'datetime' in data
    assert data['datetime'] == DATETIME.strftime(dt_format)
    assert 'time' in data
    assert data['time'] == TIME.strftime(t_format)
    assert 'money' in data
    assert data['money'] == decimal_format.format(MONEY)

    # Check if we got ISO date/time if there is no format at all
    i = get_instance(FlatModel)

    i.date_format = None
    i.datetime_format = None
    i.time_format = None

    data = i.to_dict()

    assert 'date' in data
    assert data['date'] == DATE.isoformat()
    assert 'datetime' in data
    assert data['datetime'] == DATETIME.isoformat()
    assert 'time' in data
    assert data['time'] == TIME.isoformat()


def test_default_only_param(get_instance):
    i = get_instance(FlatModel)
    i.serialize_only = ('id', 'string', 'datetime', '_protected_method', 'prop')
    data = i.to_dict()

    assert 'id' in data
    assert data['id'] == i.id
    assert 'string' in data
    assert data['string'] == i.string
    assert 'datetime' in data   # No need to check formatted value
    assert '_protected_method' in data
    assert data['_protected_method'] == i._protected_method()
    assert 'prop' in data
    assert data['prop'] == i.prop
    # Check if there is no other keys
    assert len(data.keys()) == 5


def test_default_rules_param(get_instance):
    i = get_instance(FlatModel)
    i.serialize_rules = ('-id', '_protected_method', 'prop', 'list', 'dict', 'set')
    data = i.to_dict()

    # Check SQLAlchemy fields
    assert 'id' not in data   # is excluded in rules
    assert 'string' in data
    assert data['string'] == i.string
    assert 'date' in data
    assert 'time' in data
    assert 'datetime' in data
    assert 'bool' in data
    assert data['bool'] == i.bool
    assert 'null' in data
    assert data['null'] is None

    # Check non SQL fields included in rules
    assert '_protected_method' in data
    assert data['_protected_method'] == i._protected_method()
    assert 'prop' in data
    assert data['prop'] == i.prop
    assert 'list' in data
    assert data['list'] == i.list
    assert 'dict' in data
    assert data['dict'] == i.dict
    # Serializer converts all iterables to lists
    assert 'set' in data
    assert isinstance(data['set'], list)
    assert data['set'] == list(i.set)


def test_default_rules_and_only_params(get_instance):
    i = get_instance(FlatModel)
    i.serialize_only = ('id', 'string', 'method', 'list', 'dict', 'set')
    i.serialize_rules = ('prop',)
    data = i.to_dict()

    assert 'id' in data
    assert data['id'] == i.id
    assert 'string' in data
    assert data['string'] == i.string
    assert 'method' in data
    assert data['method'] == i.method()
    assert 'prop' in data
    assert data['prop'] == i.prop
    assert 'list' in data
    assert data['list'] == i.list
    assert 'dict' in data
    assert data['dict'] == i.dict
    # Serializer converts all iterables to lists
    assert 'set' in data
    assert isinstance(data['set'], list)
    assert data['set'] == list(i.set)
    # Check if there is no other keys
    assert len(data.keys()) == 7


def test_only_param_got_in_runtime(get_instance):
    i = get_instance(FlatModel)
    data = i.to_dict(only=('id', 'string', 'datetime', '_protected_method', 'prop'))

    assert 'id' in data
    assert data['id'] == i.id
    assert 'string' in data
    assert data['string'] == i.string
    assert 'datetime' in data   # No need to check formatted value
    assert '_protected_method' in data
    assert data['_protected_method'] == i._protected_method()
    assert 'prop' in data
    assert data['prop'] == i.prop
    # Check if there is no other keys
    assert len(data.keys()) == 5


def test_rules_param_got_in_runtime(get_instance):
    i = get_instance(FlatModel)
    data = i.to_dict(rules=('-id', '_protected_method', 'prop'))

    # Check SQLAlchemy fields
    assert 'id' not in data   # is excluded in rules
    assert 'string' in data
    assert data['string'] == i.string
    assert 'date' in data
    assert 'time' in data
    assert 'datetime' in data
    assert 'bool' in data
    assert data['bool'] == i.bool
    assert 'null' in data
    assert data['null'] is None

    # Check non SQL fields included in rules
    assert '_protected_method' in data
    assert data['_protected_method'] == i._protected_method()
    assert 'prop' in data
    assert data['prop'] == i.prop


def test_rules_and_only_params_got_in_runtime(get_instance):
    i = get_instance(FlatModel)
    data = i.to_dict(
        only=('id', 'string', 'method', 'list', 'dict', 'set'),
        rules=('prop',)
    )

    # Check that we got only 'id', 'string', 'method', 'list', 'dict', 'set' and 'prop' fields
    assert 'id' in data
    assert data['id'] == i.id
    assert 'string' in data
    assert data['string'] == i.string
    assert 'method' in data
    assert data['method'] == i.method()
    assert 'list' in data
    assert data['list'] == i.list
    assert 'dict' in data
    assert data['dict'] == i.dict
    # Serializer converts all iterables to lists
    assert 'set' in data
    assert isinstance(data['set'], list)
    assert data['set'] == list(i.set)
    assert 'prop' in data
    assert data['prop'] == i.prop
    # Check if there is no other keys
    assert len(data.keys()) == 7


def test_overlapping_of_default_and_got_in_runtime_params1(get_instance):
    i = get_instance(FlatModel)
    i.serialize_only = ('id', 'method')
    i.serialize_rules = ('_protected_method',)
    data = i.to_dict(
        only=('method', 'prop')
    )

    # Check that we got only 'method' and 'prop'
    assert 'method' in data
    assert data['method'] == i.method()
    assert 'prop' in data
    assert data['prop'] == i.prop
    # Check if there is no other keys
    assert len(data.keys()) == 2


def test_overlapping_of_default_and_got_in_runtime_params2(get_instance):
    i = get_instance(FlatModel)
    i.serialize_only = ('id', 'string')
    i.serialize_rules = ('_protected_method', 'prop')
    data = i.to_dict(
        rules=('-id', 'method', )
    )

    # Check that we got only 'method', 'string', '_protected_method', 'prop'
    assert 'id' not in data
    assert 'method' in data
    assert data['method'] == i.method()
    assert 'string' in data
    assert data['string'] == i.string
    assert '_protected_method' in data
    assert data['_protected_method'] == i._protected_method()
    assert 'prop' in data
    assert data['prop'] == i.prop


def test_rules_for_nested_dicts_and_lists(get_instance):
    i = get_instance(FlatModel)
    i.serialize_only = ('list', 'prop')
    data = i.to_dict(
        rules=('-list.key', 'dict.key2', )
    )

    # Check that we got only 'prop', 'list' without 'key' and dict with key2
    assert len(data.keys()) == 3

    assert 'list' in data
    for elm in data['list']:
        if isinstance(elm, dict):
            assert 'key' not in elm

    assert 'dict' in data
    assert 'key2' in data['dict']
    assert len(data['dict'].keys()) == 1
    assert data['dict']['key2'] == i.dict['key2']

    assert 'prop' in data
    assert data['prop'] == i.prop
