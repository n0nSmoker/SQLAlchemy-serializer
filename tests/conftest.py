import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base


DATETIME_FORMAT = '%Y-%m-%d %H:%M'
DATE_FORMAT = '%Y-%m-%d'

DB_HOST = os.environ.get('POSTGRES_HOST')
DB_PORT = os.environ.get('POSTGRES_PORT', 5432)
DB_NAME = os.environ.get('POSTGRES_DB')
DB_USER = os.environ.get('POSTGRES_USER')
DB_PASS = os.environ.get('POSTGRES_PASSWORD')


@pytest.fixture(scope='session')
def session(request):
    """Creates a new database session for a test."""
    engine = create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

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
