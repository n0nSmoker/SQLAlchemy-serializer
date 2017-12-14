import pytest

import time
from flask import url_for

from tests import logger


def test_flat_model(flat_model, session):
    m = flat_model()
    session.add(m)
    session.commit()

    # Greedy serialization
    data = m.to_dict()
    assert 'id' in data
    assert data['id'] == m.id

    assert 'string' in data
    assert data['string'] == m.string

    assert 'time_at' in data and data['time_at']
    assert 'date_at' in data and data['date_at']

    assert 'boolean' in data
    assert data['boolean'] == m.boolean

    assert 'boolean2' in data
    assert data['boolean2'] == m.boolean2

    assert 'null' in data
    assert data['null'] == m.null

    # Add default schema
    m.__schema__ = ('-time_at', '-boolean2')
    data = m.to_dict()
    assert 'id' in data
    assert data['id'] == m.id

    assert 'string' in data
    assert data['string'] == m.string

    assert 'time_at' not in data
    assert 'date_at' in data and data['date_at']

    assert 'boolean' in data
    assert data['boolean'] == m.boolean

    assert 'boolean2' not in data

    assert 'null' in data
    assert data['null'] == m.null

    # Extend schema
    data = m.to_dict(extend=('time_at', '-boolean2', '-boolean'))
    assert 'id' in data
    assert data['id'] == m.id

    assert 'string' in data
    assert data['string'] == m.string

    assert 'time_at' in data and data['time_at']
    assert 'date_at' in data and data['date_at']

    assert 'boolean' not in data
    assert 'boolean2' not in data

    assert 'null' in data
    assert data['null'] == m.null

    # Replace schema
    data = m.to_dict(schema=('date_at', 'id'))
    assert 'id' in data
    assert 'date_at' in data and data['date_at']

    assert 'time_at' not in data
    assert 'string' not in data
    assert 'boolean' not in data
    assert 'boolean2' not in data
    assert 'null' not in data


def test_nested_model_greedy(flat_model, nested_model, session):
    m = nested_model()
    m.rel = flat_model()
    session.add(m)
    session.commit()

    # No negation
    data = m.to_dict()
    assert 'id' in data
    assert data['id'] == m.id

    assert 'string' in data
    assert data['string'] == m.string

    assert 'flat_id' in data and data['flat_id']

    assert 'boolean' in data
    assert data['boolean'] == m.boolean

    assert 'rel' in data
    assert 'id' in data['rel'] and data['rel']['id'] == data['flat_id']

    assert 'string' in data['rel'] and data['rel']['string']
    assert 'time_at' in data['rel'] and data['rel']['time_at']
    assert 'date_at' in data['rel'] and data['rel']['date_at']
    assert 'boolean' in data['rel'] and data['rel']['boolean']
    assert 'boolean2' in data['rel'] and data['rel']['boolean2'] is False
    assert 'null' in data['rel'] and data['rel']['null'] is None

    # With negation
    data = m.to_dict(extend=('-id', '-string', '-rel.id'))
    assert 'id' not in data
    assert 'string' not in data
    assert 'flat_id' in data and data['flat_id']

    assert 'boolean' in data
    assert data['boolean'] == m.boolean

    assert 'rel' in data
    assert 'id' not in data['rel']

    assert 'string' in data['rel'] and data['rel']['string']
    assert 'time_at' in data['rel'] and data['rel']['time_at']
    assert 'date_at' in data['rel'] and data['rel']['date_at']
    assert 'boolean' in data['rel'] and data['rel']['boolean']
    assert 'boolean2' in data['rel'] and data['rel']['boolean2'] is False
    assert 'null' in data['rel'] and data['rel']['null'] is None


def test_nested2_model_greedy(flat_model, nested_model, session):
    m = nested_model()
    m.rel = flat_model()  # a relation
    session.add(m)
    nested = flat_model()
    session.add(nested)
    session.commit()
    m.rel.nested_rel = nested  # not a relation

    # No negation
    data = m.to_dict(extend=('rel.nested_rel',))
    assert 'rel' in data
    assert 'id' in data['rel'] and data['rel']['id'] == m.rel.id
    assert 'string' in data['rel'] and data['rel']['string'] == m.rel.string
    assert 'nested_rel' in data['rel']
    assert 'id' in data['rel']['nested_rel']
    assert data['rel']['nested_rel']['id'] == m.rel.nested_rel.id
    assert 'string' in data['rel']['nested_rel']
    assert data['rel']['nested_rel']['string'] == m.rel.nested_rel.string

    # Negation
    m.rel.__schema__ = ('nested_rel',)  # because its not defined in model
    data = m.to_dict(extend=(
        '-rel.nested_rel.string',
        '-rel.nested_rel.date_at',
        '-rel.id',
    ))
    assert 'rel' in data
    assert 'nested_rel' in data['rel']
    assert 'id' in data['rel']['nested_rel']
    assert data['rel']['nested_rel']['id'] == m.rel.nested_rel.id
    assert 'string' not in data['rel']['nested_rel']
    assert 'date_at' not in data['rel']['date_at']
    assert 'id' not in data['rel']











