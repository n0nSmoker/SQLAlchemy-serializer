from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin


DATETIME = datetime(year=2018, month=1, day=1, hour=1, minute=1, second=1, microsecond=123)
DATE = DATETIME.date()
TIME = DATETIME.time()

Base = declarative_base()


class FlatModel(Base, SerializerMixin):
    __tablename__ = 'flat_model'
    serialize_only = ()
    serialize_rules = ()

    id = sa.Column(sa.Integer, primary_key=True)
    string = sa.Column(sa.String(256), default='Some string with')
    date = sa.Column(sa.Date, default=DATETIME)
    datetime = sa.Column(sa.DateTime, default=DATETIME)
    time = sa.Column(sa.Time, default=TIME)
    bool = sa.Column(sa.Boolean, default=True)
    null = sa.Column(sa.String)
    list = [1, 'test_string', .9, {'key': 123, 'key2': 23423}, {'key': 234}]
    set = {1, 2, 'test_string'}
    dict = dict(key=123, key2={'key': 12})

    @property
    def prop(self):
        return 'Some property'

    def method(self):
        return f'User defined method + {self.string}'

    def _protected_method(self):
        return f'User defined protected method + {self.string}'


class NestedModel(Base, SerializerMixin):
    __tablename__ = 'nested_model'
    serialize_only = ()
    serialize_rules = ()

    id = sa.Column(sa.Integer, primary_key=True)
    string = sa.Column(sa.String(256), default='(NESTED)Some string with')
    date = sa.Column(sa.Date, default=DATETIME)
    datetime = sa.Column(sa.DateTime, default=DATETIME)
    time = sa.Column(sa.Time, default=TIME)
    bool = sa.Column(sa.Boolean, default=False)
    null = sa.Column(sa.String)
    list = [1, '(NESTED)test_string', .9, {'key': 123}]
    set = {1, 2, '(NESTED)test_string'}
    dict = dict(key=123)

    model_id = sa.Column(sa.Integer, sa.ForeignKey('flat_model.id'))
    model = relationship('FlatModel')

    @property
    def prop(self):
        return '(NESTED)Some property'

    def method(self):
        return f'(NESTED)User defined method + {self.string}'

    def _protected_method(self):
        return f'(NESTED)User defined protected method + {self.string}'
