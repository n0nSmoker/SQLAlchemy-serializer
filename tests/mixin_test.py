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


def test_simple_model_exclusive_schema(simple_model_with_nosql_field):
    m = simple_model_with_nosql_field
    data = m.to_dict(only=('id',))
    assert len(data.keys()) == 1
    assert 'id' in data and data['id'] == m.id


def test_simple_model_exclusive_schema2(simple_model_with_nosql_field):
    m = simple_model_with_nosql_field
    data = m.to_dict(only=('nosql_field.id', 'id'))
    assert len(data.keys()) == 2
    assert 'id' in data and data['id'] == m.id
    assert 'nosql_field' in data
    assert data['nosql_field'] and isinstance(data['nosql_field'], list)
    assert 'id' in data['nosql_field'][0]
    assert data['nosql_field'][0]['id'] == m.nosql_field[0].id
    assert len(data['nosql_field'][0].keys()) == 1


def test_simple_model_extended_schema(simple_model_with_nosql_field):
    m = simple_model_with_nosql_field
    data = m.to_dict(extend=('-nosql_field', '_protected_method'))
    assert 'id' in data and data['id'] == m.id
    assert 'string' in data and data['string'] == m.string
    assert 'time_at' in data and data['time_at']
    assert 'date_at' in data and data['date_at']
    assert 'boolean' in data and data['boolean'] == m.boolean
    assert 'null' in data and data['null'] == m.null
    assert 'nosql_field' not in data


def test_complex_model_no_schema(complex_model):
    m = complex_model
    data = m.to_dict()
    assert 'id' in data and data['id'] == m.id
    assert 'string' in data and data['string'] == m.string
    assert 'boolean' in data and data['boolean'] == m.boolean
    assert 'null' in data and data['null'] == m.null
    assert 'rel_id' in data and data['rel_id'] == m.rel_id
    assert 'rel' in data and data['rel']
    data = data['rel']
    assert 'id' in data and data['id'] == m.rel.id
    assert 'string' in data and data['string'] == m.rel.string
    assert 'boolean' in data and data['boolean'] == m.rel.boolean
    assert 'null' in data and data['null'] == m.rel.null
    assert 'rel' in data and data['rel']
    assert isinstance(data['rel'], list)
    data = data['rel'][0]
    assert 'id' in data and data['id'] == m.rel.rel[0].id
    assert 'string' in data and data['string'] == m.rel.rel[0].string
    assert 'time_at' in data and data['time_at']
    assert 'date_at' in data and data['date_at']
    assert 'boolean' in data and data['boolean'] == m.rel.rel[0].boolean
    assert 'null' in data and data['null'] == m.rel.rel[0].null


def test_complex_model_mixed_schema(complex_model):
    m = complex_model
    data = m.to_dict(only=('rel', 'rel.rel', '-rel.rel.id'))
    assert 'rel' in data and data['rel']
    assert len(data.keys()) == 1
    assert 'rel' in data['rel'] and data['rel']['rel']
    assert len(data['rel'].keys()) == 1
    assert isinstance(data['rel']['rel'], list)
    data = data['rel']['rel'][0]
    assert 'id' not in data
    assert 'string' in data and data['string'] == m.rel.rel[0].string
    assert 'time_at' in data and data['time_at']
    assert 'date_at' in data and data['date_at']
    assert 'boolean' in data and data['boolean'] == m.rel.rel[0].boolean
    assert 'null' in data and data['null'] == m.rel.rel[0].null


def test_complex_model_exclusive_schema(complex_model):
    m = complex_model
    data = m.to_dict(only=('id', 'rel.rel.id'))
    assert len(data.keys()) == 2
    assert 'id' in data and data['id'] == m.id
    assert 'rel' in data
    assert len(data['rel'].keys()) == 1
    assert 'rel' in data['rel'] and data['rel']['rel']
    assert isinstance(data['rel']['rel'], list) and data['rel']['rel']
    data = data['rel']['rel'][0]
    assert 'id' in data and data['id'] == m.rel.rel[0].id
    assert len(data.keys()) == 1


def test_complex_model_exclusive2_schema(complex_model):
    m = complex_model
    data = m.to_dict(only=('id',), extend=('rel.rel.id',))
    assert len(data.keys()) == 2
    assert 'id' in data and data['id'] == m.id
    assert 'rel' in data
    assert len(data['rel'].keys()) == 1
    assert 'rel' in data['rel'] and data['rel']['rel']
    assert isinstance(data['rel']['rel'], list) and data['rel']['rel']
    data = data['rel']['rel'][0]
    assert 'id' in data and data['id'] == m.rel.rel[0].id
    assert len(data.keys()) == 1


def test_complex_model_extend_schema(complex_model):
    m = complex_model
    data = m.to_dict(extend=('-rel.rel.id', 'rel.rel._protected_method', 'rel.rel.nosql_field', '-id'))
    assert 'id' not in data
    assert 'string' in data and data['string'] == m.string
    assert 'boolean' in data and data['boolean'] == m.boolean
    assert 'null' in data and data['null'] == m.null
    assert 'rel_id' in data and data['rel_id'] == m.rel_id
    assert 'rel' in data and data['rel']
    data = data['rel']
    assert 'id' in data and data['id'] == m.rel.id
    assert 'string' in data and data['string'] == m.rel.string
    assert 'boolean' in data and data['boolean'] == m.rel.boolean
    assert 'null' in data and data['null'] == m.rel.null
    assert 'rel' in data and data['rel']
    assert isinstance(data['rel'], list)
    data = data['rel'][0]
    assert 'id' not in data
    assert 'string' in data and data['string'] == m.rel.rel[0].string
    assert 'time_at' in data and data['time_at']
    assert 'date_at' in data and data['date_at']
    assert 'boolean' in data and data['boolean'] == m.rel.rel[0].boolean
    assert 'null' in data and data['null'] == m.rel.rel[0].null
    assert '_protected_method' in data and data['_protected_method'] == m.rel.rel[0]._protected_method()
    assert 'nosql_field' in data

