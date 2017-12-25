import pytest
from tests import logger


def test_simple_model_no_schema(simple_model_with_nosql_field):
    m = simple_model_with_nosql_field
    data = m.to_dict()
    assert 'id' in data and data['id'] == m.id
    assert 'string' in data and data['string'] == m.string
    assert 'time_at' in data and data['time_at']
    assert 'date_at' in data and data['date_at']
    assert 'boolean' in data and data['boolean'] == m.boolean
    assert 'null' in data and data['null'] == m.null
    assert 'nosql_field' in data and len(data['nosql_field']) == 1
    data = data['nosql_field'][0]
    assert 'id' in data and data['id'] == m.nosql_field[0].id
    assert 'string' in data and data['string'] == m.nosql_field[0].string
    assert 'time_at' in data and data['time_at']
    assert 'date_at' in data and data['date_at']
    assert 'boolean' in data and data['boolean'] == m.nosql_field[0].boolean
    assert 'null' in data and data['null'] == m.nosql_field[0].null


def test_simple_model_mixed_schema(simple_model_with_nosql_field):
    m = simple_model_with_nosql_field
    data = m.to_dict(only=('nosql_field', '-nosql_field.id'))
    assert len(data.keys()) == 1
    assert 'nosql_field' in data and len(data['nosql_field']) == 1
    data = data['nosql_field'][0]
    assert 'id' not in data
    assert 'string' in data and data['string'] == m.nosql_field[0].string
    assert 'time_at' in data and data['time_at']
    assert 'date_at' in data and data['date_at']
    assert 'boolean' in data and data['boolean'] == m.nosql_field[0].boolean
    assert 'null' in data and data['null'] == m.nosql_field[0].null


# def test_simple_flat_madel_with_default_schema_positive(flat_model):
#     m = flat_model
#     m.__schema_only__ = ('time_at', 'boolean2')
#     data = m.to_dict()
#     assert 'id' not in data
#     assert 'string' not in data
#     assert 'date_at' not in data
#     assert 'boolean' not in data
#     assert 'null' not in data
#
#     assert 'time_at' in data
#     assert 'boolean2' in data
#
#
# def test_simple_flat_madel_with_default_schema_negative(flat_model):
#     m = flat_model
#     m.__schema_only__ = ()
#     m.__schema_extend__ = ('-time_at', '-boolean2')
#     data = m.to_dict()
#     assert 'time_at' not in data
#     assert 'boolean2' not in data
#
#     assert 'id' in data and data['id'] == m.id
#     assert 'string' in data and data['string'] == m.string
#     assert 'date_at' in data and data['date_at']
#     assert 'boolean' in data and data['boolean'] == m.boolean
#     assert 'null' in data and data['null'] == m.null
#
#
# def test_simple_flat_madel_with_extend(flat_model):
#     m = flat_model
#     m.__schema_extend__ = ('-time_at', '-boolean2')
#
#     data = m.to_dict(extend=('time_at', '-boolean'))
#     assert 'id' in data
#     assert data['id'] == m.id
#
#     assert 'string' in data
#     assert data['string'] == m.string
#
#     assert 'time_at' in data and data['time_at']
#     assert 'date_at' in data and data['date_at']
#
#     assert 'boolean' not in data
#     assert 'boolean2' not in data
#
#     assert 'null' in data
#     assert data['null'] == m.null
#
#
# def test_simple_flat_madel_with_replace(flat_model):
#     m = flat_model
#     data = m.to_dict(only=('date_at', 'id'))
#     assert 'id' in data
#     assert 'date_at' in data and data['date_at']
#
#     assert 'time_at' not in data
#     assert 'string' not in data
#     assert 'boolean' not in data
#     assert 'boolean2' not in data
#     assert 'null' not in data
#
#
# def test_simple_nested_model_with_no_schema(simple_nested_model):
#     m = simple_nested_model
#     data = m.to_dict()
#     assert 'id' in data
#     assert data['id'] == m.id
#
#     assert 'string' in data
#     assert data['string'] == m.string
#
#     assert 'flat_id' in data and data['flat_id']
#
#     assert 'boolean' in data
#     assert data['boolean'] == m.boolean
#
#     assert 'rel' in data
#     assert 'id' in data['rel'] and data['rel']['id'] == data['flat_id']
#
#     assert 'string' in data['rel'] and data['rel']['string']
#     assert 'time_at' in data['rel'] and data['rel']['time_at']
#     assert 'date_at' in data['rel'] and data['rel']['date_at']
#     assert 'boolean' in data['rel'] and data['rel']['boolean']
#     assert 'boolean2' in data['rel'] and data['rel']['boolean2'] is False
#     assert 'null' in data['rel'] and data['rel']['null'] is None
#
#
# def test_simple_nested_model_with_extend(simple_nested_model):
#     m = simple_nested_model
#     data = m.to_dict(extend=('-id', '-string', '-rel.id'))
#     assert 'id' not in data
#     assert 'string' not in data
#     assert 'flat_id' in data and data['flat_id']
#
#     assert 'boolean' in data
#     assert data['boolean'] == m.boolean
#
#     assert 'rel' in data
#     assert 'id' not in data['rel']
#
#     assert 'string' in data['rel'] and data['rel']['string']
#     assert 'time_at' in data['rel'] and data['rel']['time_at']
#     assert 'date_at' in data['rel'] and data['rel']['date_at']
#     assert 'boolean' in data['rel'] and data['rel']['boolean']
#     assert 'boolean2' in data['rel'] and data['rel']['boolean2'] is False
#     assert 'null' in data['rel'] and data['rel']['null'] is None
#
#
# def test_simple_nested_model_with_default_schema(simple_nested_model):
#     m = simple_nested_model
#     m.__schema_extend__ = ('-id', 'string', '-rel.id')
#     data = m.to_dict()
#     assert 'id' not in data
#     assert 'flat_id' in data and data['flat_id']
#
#     assert 'string' in data and data['string'] == m.string
#     assert 'boolean' in data and data['boolean'] == m.boolean
#
#     assert 'rel' in data
#     assert 'id' not in data['rel']
#
#     assert 'string' in data['rel'] and data['rel']['string']
#     assert 'time_at' in data['rel'] and data['rel']['time_at']
#     assert 'date_at' in data['rel'] and data['rel']['date_at']
#     assert 'boolean' in data['rel'] and data['rel']['boolean']
#     assert 'boolean2' in data['rel'] and data['rel']['boolean2'] is False
#     assert 'null' in data['rel'] and data['rel']['null'] is None
#
#
# def test_nested2_model_with_extend_positive(nested_model):
#     m = nested_model
#     data = m.to_dict(extend=('rel.nested_rel',))
#     assert 'rel' in data
#     assert 'id' in data['rel'] and data['rel']['id'] == m.rel.id
#     assert 'string' in data['rel'] and data['rel']['string'] == m.rel.string
#     assert 'nested_rel' in data['rel']
#     assert 'id' in data['rel']['nested_rel']
#     assert data['rel']['nested_rel']['id'] == m.rel.nested_rel.id
#     assert 'string' in data['rel']['nested_rel']
#     assert data['rel']['nested_rel']['string'] == m.rel.nested_rel.string
#
#
# def test_nested2_model_with_extend_negative(nested_model):
#     m = nested_model
#     m.rel.__schema_extend__ = ('nested_rel',)  # because its not defined in model
#     data = m.to_dict(extend=(
#         '-rel.nested_rel.string',
#         '-rel.nested_rel.date_at',
#         '-rel.id',
#     ))
#     assert 'rel' in data
#     assert 'nested_rel' in data['rel']
#     assert 'id' in data['rel']['nested_rel']
#     assert data['rel']['nested_rel']['id'] == m.rel.nested_rel.id
#     assert 'string' not in data['rel']['nested_rel']
#     assert 'date_at' not in data['rel']['date_at']
#     assert 'id' not in data['rel']
#
#
# def test_nested2_model_with_schema(nested_model):
#     m = nested_model
#     # Fetch one property only
#     data = m.to_dict(only=('rel.nested_rel.id',))
#     assert 'rel' in data and len(data.keys()) == 1
#     assert 'nested_rel' in data['rel'] and len(data['rel'].keys()) == 1
#     assert 'id' in data['rel']['nested_rel']
#     assert data['rel']['nested_rel']['id'] == m.rel.nested_rel.id
#     assert len(data['rel']['nested_rel'].keys()) == 1
#
#     # Fetch two property only
#     data = m.to_dict(only=('rel.nested_rel.id', 'rel.nested_rel.string'))
#     assert 'rel' in data and len(data.keys()) == 1
#     assert 'nested_rel' in data['rel'] and len(data['rel'].keys()) == 1
#     assert 'id' in data['rel']['nested_rel']
#     assert data['rel']['nested_rel']['id'] == m.rel.nested_rel.id
#     assert 'string' in data['rel']['nested_rel']
#     assert data['rel']['nested_rel']['string'] == m.rel.nested_rel.string
#     assert len(data['rel']['nested_rel'].keys()) == 2
#
#
# def test_nested2_model_with_non_sql_list_field_no_schema(nested_model, flat_models_list):
#     m = nested_model
#     m.non_sql_field = flat_models_list
#
#     data = m.to_dict()
#     assert 'non_sql_field' not in data
#     assert 'id' in data and data['id'] == m.id
#
#
# def test_nested2_model_with_non_sql_list_field_default_schema(nested_model, flat_models_list):
#     m = nested_model
#     m.non_sql_field = flat_models_list
#
#     m.__schema_only__ = ('non_sql_field',)
#     data = m.to_dict()
#     assert 'id' not in data
#     assert 'non_sql_field' in data
#     assert len(data['non_sql_field']) == 5
#     assert 'id' in data['non_sql_field'][0] and data['non_sql_field'][0]['id']
#     assert 'string' in data['non_sql_field'][0]
#     assert data['non_sql_field'][0]['string'] == '0'
#     assert data['non_sql_field'][1]['string'] == '1'
#
#
# def test_nested2_model_with_non_sql_list_field_with_extend(nested_model, flat_models_list):
#     m = nested_model
#     m.non_sql_field = flat_models_list
#     m.__schema_only__ = ('non_sql_field',)
#     data = m.to_dict(extend=('-non_sql_field.string', 'id'))
#     assert 'id' in data and data['id']
#     assert 'non_sql_field' in data
#     assert len(data['non_sql_field']) == 5
#     assert 'string' not in data['non_sql_field'][0]
#     assert 'id' in data['non_sql_field'][0]
#
#
# def test_nested_model_with_nested_default_schema_only(nested_model, flat_models_list):
#     m = nested_model
#     m.rel.__schema_only__ = ('string',)
#     data = m.to_dict()
#     assert 'id' in data and data['id']
#     assert 'string' in data
#     assert 'boolean' in data
#     assert 'null' in data
#     assert 'flat_id' in data
#     assert 'rel' in data
#     assert 'string' in data['rel']
#     assert len(data['rel'].keys()) == 1
#
#
# def test_nested_model_with_default_exclusive_schema_on_every_level(nested_model):
#     m = nested_model
#     m.__schema_only__ = ('rel',)
#     m.rel.__schema_only__ = ('string',)
#     data = m.to_dict()
#     assert 'rel' in data and data['rel']
#     assert len(data.keys()) == 1
#     assert 'string' in data['rel']
#     assert len(data['rel'].keys()) == 1
#
#
# def test_m2m_model_with_default_exclusive_schema(m2m_model):
#     m = m2m_model
#     m.__schema_only__ = ('rel',)
#     data = m.to_dict()
#     assert 'rel' in data and data['rel']
#     assert len(data.keys()) == 1
#     assert len(data['rel']) == 1
#     assert 'rel' in data['rel'][0]
#     assert len(data['rel'][0].keys()) == 1
#     assert 'string' in data['rel'][0]['rel']
#     assert len(data['rel'][0]['rel'].keys()) == 1
#
#
# def test_m2m_model_with_default_exclusive_schema_with_extend(m2m_model):
#     m = m2m_model
#     m.__schema_only__ = ('rel',)
#     data = m.to_dict(extend=('id', 'rel.id', 'rel.rel.id'))
#     assert 'rel' in data and data['rel']
#     assert 'id' in data and data['id']
#     assert len(data.keys()) == 2
#     assert len(data['rel']) == 1
#     assert 'rel' in data['rel'][0]
#     assert 'id' in data['rel'][0]
#     assert len(data['rel'][0].keys()) == 2
#     assert 'string' in data['rel'][0]['rel']
#     assert 'id' in data['rel'][0]['rel']
#     assert len(data['rel'][0]['rel'].keys()) == 2
#
#
#
#
#
#
#
#
#
#
#
