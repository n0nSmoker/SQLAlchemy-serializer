import os
import pytest
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy_serializer.serializer import Serializer
from .models import Base


logger = logging.getLogger("serializer")
logger.setLevel(logging.DEBUG)


DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_TIME_FORMAT = "%H:%M"
DEFAULT_DECIMAL_FORMAT = "{}"


DB_HOST = os.environ.get("POSTGRES_HOST")
DB_PORT = os.environ.get("POSTGRES_PORT", 5432)
DB_NAME = os.environ.get("POSTGRES_DB")
DB_USER = os.environ.get("POSTGRES_USER")
DB_PASS = os.environ.get("POSTGRES_PASSWORD")


@pytest.fixture(scope="session")
def session(request):
    """Creates a new database session for a test."""
    engine = create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    maker = sessionmaker(bind=engine)
    session = maker()

    Base.metadata.drop_all(
        bind=engine
    )  # Flush DATABASE before use (in case of reused container)
    Base.metadata.create_all(bind=engine)

    def teardown():
        session.close()

    request.addfinalizer(teardown)

    return session


@pytest.fixture(scope="session")
def get_instance(session):
    def func(model, **kwargs):
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance

    return func


@pytest.fixture()
def get_serializer():
    def func(
        date_format=DEFAULT_DATE_FORMAT,
        datetime_format=DEFAULT_DATETIME_FORMAT,
        time_format=DEFAULT_TIME_FORMAT,
        decimal_format=DEFAULT_DECIMAL_FORMAT,
        tzinfo=None,
        serialize_types=(),
        skip_none_values=None,
    ):
        return Serializer(
            date_format=date_format,
            datetime_format=datetime_format,
            time_format=time_format,
            decimal_format=decimal_format,
            tzinfo=tzinfo,
            serialize_types=serialize_types,
            skip_none_values=skip_none_values,
        )

    return func
