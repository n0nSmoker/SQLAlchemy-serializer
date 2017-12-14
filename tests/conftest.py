import pytest

from datetime import datetime
from flask import url_for
from werkzeug.utils import import_string

from flask_builder import create_app, create_db, drop_db, create_tables, get_config_name, db
from sqlalchemy_serializer import SerializerMixin

APP_NAME = 'serializer_tests'


class FlatModel(db.Model, SerializerMixin):
    __tablename__ = 'test_flat_model'
    id = db.Column(db.Integer, primary_key=True)
    string = db.Column(db.String(256), default='Some string with КИРИЛИК СИМБОЛЗ!')
    time_at = db.Column(db.DateTime, default=datetime.utcnow())
    date_at = db.Column(db.Date, default=datetime.utcnow())
    boolean = db.Column(db.Boolean, default=True)
    boolean2 = db.Column(db.Boolean, default=False)
    null = db.Column(db.String)


class NestedModel(db.Model, SerializerMixin):
    __tablename__ = 'test_nested_model'
    id = db.Column(db.Integer, primary_key=True)
    string = db.Column(db.String(256), default='Some string with КИРИЛИК СИМБОЛЗ!')
    boolean = db.Column(db.Boolean, default=True)
    null = db.Column(db.String)
    flat_id = db.Column(db.ForeignKey('test_flat_model.id', ondelete='CASCADE'))
    rel = db.relationship('FlatModel', lazy='joined', uselist=False)


@pytest.fixture(scope='module')
def app(request):
    """Session-wide test `Flask` application."""
    # Create DB
    # config = import_string(get_config_name())
    # dsn = config.SQLALCHEMY_DATABASE_URI
    # dsn = dsn[:dsn.rfind('/')] + '/%s' % APP_NAME.lower()  # Change DB-name
    config = {}
    dsn = 'postgresql+psycopg2://postgres:root!@localhost:5432/serializer_mixin_test'
    drop_db(dsn)
    create_db(dsn)

    # Create app
    config['TESTING'] = True
    config['SQLALCHEMY_DATABASE_URI'] = dsn
    config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app = create_app(name=APP_NAME, config=config)

    # Establish an application context before running the tests.
    ctx = app.app_context()
    ctx.push()

    create_tables(app)  # Only after context was pushed

    # Add test client
    app.client = app.test_client()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app


@pytest.fixture(scope='module')
def session(app, request):
    """Creates a new database session for a test."""
    connection = app.db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = app.db.create_scoped_session(options=options)

    app.db.session = session

    def teardown():
        transaction.rollback()
        connection.close()
        session.remove()

    request.addfinalizer(teardown)
    return session


@pytest.fixture(scope='function')
def flat_model(session):
    m = FlatModel()
    session.add(m)
    session.commit()
    return m


@pytest.fixture(scope='function')
def flat_models_list(session):
    result = []
    for i in range(5):
        m = FlatModel(string=i)
        session.add(m)
        result.append(m)
    session.commit()
    return result


@pytest.fixture(scope='function')
def simple_nested_model(flat_model, session):
    m = NestedModel()
    m.rel = flat_model
    session.add(m)
    session.commit()
    return m


@pytest.fixture(scope='function')
def nested_model(session):
    m = NestedModel()
    m.rel = FlatModel()  # a relation
    session.add(m)

    nested = FlatModel()
    session.add(nested)
    session.commit()
    m.rel.nested_rel = nested  # not a relation
    return m



