from .models import FlatModel, NestedModel, DATETIME, TIME, DATE


def test_no_defaults_no_rules(get_instance):
    """
    Checks to_dict method of model with no predefined options
    :param get_instance:
    :return:
    """
    i = get_instance(NestedModel, model_id=get_instance(FlatModel).id)
    data = i.to_dict()

    # Check nested SQLAlchemy fields
    assert 'model' in data
    nested = data['model']

    assert 'id' in nested
    assert 'string' in nested
    assert nested['string'] == i.model.string
    assert 'date' in nested
    assert 'time' in nested
    assert 'datetime' in nested
    assert 'bool' in nested
    assert nested['bool'] == i.model.bool
    assert 'null' in nested
    assert nested['null'] is None

    # Check non-sql fields (not included in this case, need to be defined explicitly)
    assert 'list' not in nested
    assert 'set' not in nested
    assert 'dict' not in nested
    assert 'prop' not in nested
    assert 'method' not in nested
    assert '_protected_method' not in nested


def test_datetime_default_formats(get_instance):
    """
    Check date/datetime/time default formats in resulting JSON of model with no predefined options
    :param get_instance:
    :return:
    """
    i = get_instance(NestedModel, model_id=get_instance(FlatModel).id)
    # Default formats
    d_format = i.date_format
    dt_format = i.datetime_format
    t_format = i.time_format
    data = i.to_dict()

    assert 'model' in data
    nested = data['model']

    assert 'date' in nested
    assert nested['date'] == DATE.strftime(d_format)
    assert 'datetime' in data
    assert nested['datetime'] == DATETIME.strftime(dt_format)
    assert 'time' in data
    assert nested['time'] == TIME.strftime(t_format)


def test_datetime_formats_got_in_runtime(get_instance):
    """
    Check date/datetime/time default formats in resulting JSON of flat model got as the parameters of to_dict func
    :param get_instance:
    :return:
    """
    d_format = '%Y/%m/%d'
    dt_format = '%Y/%m/%d %H:%M'
    t_format = '>%H<'

    i = get_instance(NestedModel, model_id=get_instance(FlatModel).id)

    # Check that default formats are different
    assert d_format != i.date_format
    assert dt_format != i.datetime_format
    assert t_format != i.time_format

    data = i.to_dict(
        date_format=d_format,
        datetime_format=dt_format,
        time_format=t_format,
    )
    assert 'model' in data
    nested = data['model']

    # Check serialized formats
    assert 'date' in nested
    assert nested['date'] == DATE.strftime(d_format)
    assert 'datetime' in data
    assert nested['datetime'] == DATETIME.strftime(dt_format)
    assert 'time' in data
    assert nested['time'] == TIME.strftime(t_format)


def test_default_only_param(get_instance):
    i = get_instance(NestedModel, model_id=get_instance(FlatModel).id)
    i.serialize_only = (
        'model.id', 'model.string', 'model.datetime', 'model._protected_method', 'model.prop'
    )
    data = i.to_dict()

    # Check if there is no other keys
    assert len(data.keys()) == 1

    assert 'model' in data
    nested = data['model']

    assert 'id' in nested
    assert nested['id'] == i.model.id
    assert 'string' in nested
    assert nested['string'] == i.model.string
    assert 'datetime' in nested   # No need to check formatted value
    assert '_protected_method' in nested
    assert nested['_protected_method'] == i.model._protected_method()
    assert 'prop' in nested
    assert nested['prop'] == i.model.prop
    # Check if there is no other keys
    assert len(nested.keys()) == 5


def test_default_rules_param(get_instance):
    i = get_instance(NestedModel, model_id=get_instance(FlatModel).id)
    i.serialize_rules = (
        '-model.id', 'model._protected_method', 'model.prop', 'model.list', 'model.dict', 'model.set'
    )
    data = i.to_dict()
    assert 'model' in data
    nested = data['model']

    # Check SQLAlchemy fields
    assert 'id' not in nested   # is excluded in rules
    assert 'string' in nested
    assert nested['string'] == i.model.string
    assert 'date' in nested
    assert 'time' in nested
    assert 'datetime' in nested
    assert 'bool' in nested
    assert nested['bool'] == i.model.bool
    assert 'null' in nested
    assert nested['null'] is None

    # Check non SQL fields included in rules
    assert '_protected_method' in nested
    assert nested['_protected_method'] == i.model._protected_method()
    assert 'prop' in nested
    assert nested['prop'] == i.model.prop
    assert 'list' in nested
    assert nested['list'] == i.model.list
    assert 'dict' in nested
    assert nested['dict'] == i.model.dict
    # Serializer converts all iterables to lists
    assert 'set' in nested
    assert isinstance(nested['set'], list)
    assert nested['set'] == list(i.model.set)


def test_default_rules_and_only_params(get_instance):
    i = get_instance(NestedModel, model_id=get_instance(FlatModel).id)
    i.serialize_only = (
        'model.id', 'model.string', 'model.method', 'model.list', 'model.dict', 'model.set'
    )
    i.serialize_rules = ('model.prop',)
    data = i.to_dict()
    assert 'model' in data
    nested = data['model']

    assert 'id' in nested
    assert nested['id'] == i.model.id
    assert 'string' in nested
    assert nested['string'] == i.model.string
    assert 'method' in nested
    assert nested['method'] == i.model.method()
    assert 'prop' in nested
    assert nested['prop'] == i.model.prop
    assert 'list' in nested
    assert nested['list'] == i.model.list
    assert 'dict' in nested
    assert nested['dict'] == i.model.dict
    # Serializer converts all iterables to lists
    assert 'set' in nested
    assert isinstance(nested['set'], list)
    assert nested['set'] == list(i.model.set)
    # Check if there is no other keys
    assert len(nested.keys()) == 7


def test_only_param_got_in_runtime(get_instance):
    i = get_instance(NestedModel, model_id=get_instance(FlatModel).id)
    data = i.to_dict(
        only=('id', 'model.id', 'model.string', 'model.datetime', 'model._protected_method', 'model.prop')
    )

    assert 'id' in data
    assert len(data.keys()) == 2
    assert 'model' in data
    nested = data['model']

    assert 'id' in nested
    assert nested['id'] == i.model.id
    assert 'string' in nested
    assert nested['string'] == i.model.string
    assert 'datetime' in nested   # No need to check formatted value
    assert '_protected_method' in nested
    assert nested['_protected_method'] == i.model._protected_method()
    assert 'prop' in nested
    assert nested['prop'] == i.model.prop
    # Check if there is no other keys
    assert len(nested.keys()) == 5


def test_rules_param_got_in_runtime(get_instance):
    i = get_instance(NestedModel, model_id=get_instance(FlatModel).id)
    data = i.to_dict(rules=('-id', 'prop', '-model.id', 'model._protected_method', 'model.prop'))

    assert 'id' not in data
    assert 'prop' in data    # Non SQL field here because it was mentioned in rules
    assert 'string' in data  # SQL field here because all model's fields here by default
    nested = data['model']

    # Check SQLAlchemy fields
    assert 'id' not in nested   # is excluded in rules
    assert 'string' in nested
    assert nested['string'] == i.model.string
    assert 'date' in nested
    assert 'time' in nested
    assert 'datetime' in nested
    assert 'bool' in nested
    assert nested['bool'] == i.model.bool
    assert 'null' in nested
    assert nested['null'] is None

    # Check non SQL fields included in rules
    assert '_protected_method' in nested
    assert nested['_protected_method'] == i.model._protected_method()
    assert 'prop' in nested
    assert nested['prop'] == i.model.prop


def test_rules_and_only_params_got_in_runtime(get_instance):
    i = get_instance(NestedModel, model_id=get_instance(FlatModel).id)
    data = i.to_dict(
        only=('model.id', 'model.string', 'model.method', 'model.set'),
        rules=('id', 'model.prop',)
    )

    assert 'id' in data
    assert len(data.keys()) == 2

    assert 'model' in data
    nested = data['model']

    assert 'id' in nested
    assert nested['id'] == i.model.id
    assert 'string' in nested
    assert nested['string'] == i.model.string
    assert 'method' in nested
    assert nested['method'] == i.model.method()
    # Serializer converts all iterables to lists
    assert 'set' in nested
    assert isinstance(nested['set'], list)
    assert nested['set'] == list(i.model.set)
    assert 'prop' in nested
    assert nested['prop'] == i.model.prop
    # Check if there is no other keys
    assert len(nested.keys()) == 5


def test_overlapping_of_default_and_got_in_runtime_params1(get_instance):
    i = get_instance(NestedModel, model_id=get_instance(FlatModel).id)
    i.serialize_only = ('model.id', 'model.method')
    i.serialize_rules = ('_protected_method',)
    data = i.to_dict(
        only=('id', 'model.method', 'model.prop')   # Params passed in to_dict have HIGHEST priority
    )

    assert 'id' in data
    assert len(data.keys()) == 2

    assert 'model' in data
    nested = data['model']

    # Check that we got only 'method' and 'prop'
    assert 'method' in nested
    assert nested['method'] == i.model.method()
    assert 'prop' in nested
    assert nested['prop'] == i.model.prop
    # Check if there is no other keys
    assert len(nested.keys()) == 2


def test_overlapping_of_default_and_got_in_runtime_params2(get_instance):
    i = get_instance(NestedModel, model_id=get_instance(FlatModel).id)
    i.serialize_only = ('id', 'string')
    i.serialize_rules = ('model.prop',)
    data = i.to_dict(
        rules=('-id', 'model.method',)
    )

    assert 'id' not in data
    assert 'string' in data
    assert 'model' in data
    assert len(data.keys()) == 2

    nested = data['model']

    assert 'method' in nested
    assert nested['method'] == i.model.method()
    assert 'prop' in nested
    assert nested['prop'] == i.model.prop
    assert len(nested.keys()) == 2


def test_rules_for_nested_dicts_and_lists(get_instance):
    i = get_instance(NestedModel, model_id=get_instance(FlatModel).id)
    i.serialize_only = ('dict.key', 'model.list', 'model.prop')
    data = i.to_dict(
        rules=('-model.list.key', 'model.dict.key2', )
    )
    assert 'dict' in data
    assert 'model' in data
    assert len(data.keys()) == 2

    assert 'key' in data['dict']
    assert data['dict']['key'] == i.dict['key']
    assert len(data['dict'].keys()) == 1

    nested = data['model']

    # Check that we got only 'prop', 'list' without 'key' and dict with key2
    assert len(nested.keys()) == 3

    assert 'list' in nested
    for elm in nested['list']:
        if isinstance(elm, dict):
            assert 'key' not in elm

    assert 'dict' in nested
    assert 'key2' in nested['dict']
    assert len(nested['dict'].keys()) == 1
    assert nested['dict']['key2'] == i.model.dict['key2']

    assert 'prop' in nested
    assert nested['prop'] == i.model.prop


def test_controversial_rules(get_instance):
    i = get_instance(NestedModel, model_id=get_instance(FlatModel).id)
    i.serialize_rules = ('-model', 'model.id')
    data = i.to_dict()

    # Negative rules have higher priority
    assert 'model' not in data

    i = get_instance(NestedModel, model_id=get_instance(FlatModel).id)
    i.serialize_rules = ('-model.id',)
    i.serialize_only = ('model', 'model.string')
    data = i.to_dict()

    assert 'model' in data
    nested = data['model']

    # Rules from ONLY section always have higher priority
    assert 'id' not in nested
    assert 'string' in nested

    # Negative rules in ONLY section
    # Nice way
    i = get_instance(NestedModel, model_id=get_instance(FlatModel).id)
    i.serialize_only = ('model', '-model.string')
    data = i.to_dict()

    assert 'model' in data
    nested = data['model']
    assert 'id' in nested
    assert 'string' not in nested

    # Wrong way
    i = get_instance(NestedModel, model_id=get_instance(FlatModel).id)
    i.serialize_only = ('-model.string',)
    data = i.to_dict()

    assert not data
