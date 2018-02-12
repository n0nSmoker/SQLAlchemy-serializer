import pytest
from flask_builder import create_app, create_db, drop_db, create_tables, db, init_app

from tests import logger
from tests.models import NoRelationshipModel, Many2OneModel, Many2manyModel


APP_NAME = 'serializer_tests'


@pytest.fixture(scope='module')
def app(request):
    """Session-wide test `Flask` application."""
    # Create DB
    # config = import_string(get_config_name())
    # dsn = config.SQLALCHEMY_DATABASE_URI
    # dsn = dsn[:dsn.rfind('/')] + '/%s' % APP_NAME.lower()  # Change DB-name
    config = {}
    # dsn = 'postgresql+psycopg2://yuribro:@localhost:5432/serializer_mixin_test'

    dsn = 'postgresql+psycopg2://postgres:root!@localhost:5432/serializer_mixin_test'
    drop_db(dsn)
    create_db(dsn)

    # Create app
    config['TESTING'] = True
    config['SQLALCHEMY_DATABASE_URI'] = dsn
    config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app = create_app(name=APP_NAME)
    app = init_app(app, config=config)

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
def complex_model(session):
    m = Many2OneModel()
    m.rel = Many2manyModel()
    m.rel.rel.append(
        NoRelationshipModel()
    )
    session.add(m)
    session.commit()
    return m


@pytest.fixture(scope='function')
def simple_model_with_nosql_field(session):
    # NoSQLAlchemy field should be defined explicitly
    NoRelationshipModel.__schema_extend__ = ('nosql_field',)
    m = NoRelationshipModel()
    m1 = NoRelationshipModel()
    m.nosql_field = [m1]
    session.add(m)
    session.add(m1)
    session.commit()
    return m


@pytest.fixture(scope='function')
def simple_model_with_dict_field(session):
    # NoSQLAlchemy field should be defined explicitly
    NoRelationshipModel.__schema_extend__ = ('nosql_field',)
    m = NoRelationshipModel()
    m.nosql_field = dict(
        a=1,
        b=2,
        c=dict(
            a=22,
            b='qwerty'
        )
    )
    session.add(m)
    session.commit()
    return m

