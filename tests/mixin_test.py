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

    # Override schema
    data = m.to_dict(schema=('time_at', '-boolean2', '-boolean'))
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

    # Not Greedy
    data = m.to_dict(is_greedy=False, schema=('date_at', 'id'))
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

    # Greedy no negation
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

    # Greedy with negation
    data = m.to_dict(schema=('-id', '-string', '-rel.id'))
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









