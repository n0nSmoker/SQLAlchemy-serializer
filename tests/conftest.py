import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base


DATETIME_FORMAT = '%Y-%m-%d %H:%M'
DATE_FORMAT = '%Y-%m-%d'

db_name = 'db_name'


@pytest.fixture(scope='session')
def session(request):
    """Creates a new database session for a test."""
    engine = create_engine(f'postgresql+psycopg2://root:password@db:5432/{db_name}')

    maker = sessionmaker(bind=engine)
    session = maker()

    Base.metadata.drop_all(bind=engine)  # Flush DATABASE before use (in case of reused container)
    Base.metadata.create_all(bind=engine)

    def teardown():
        session.close()
    request.addfinalizer(teardown)

    return session


@pytest.fixture(scope='session')
def get_instance(session):
    def func(model, **kwargs):
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance
    return func
