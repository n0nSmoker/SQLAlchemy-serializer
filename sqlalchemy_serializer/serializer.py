from datetime import datetime, date, time
import logging
import inspect

from collections import Iterable
from types import MethodType

from sqlalchemy import inspect as sql_inspect

from .lib.utils import get_type
from .lib.timezones import to_local_time, format_dt
from .lib.rules import Schema


logger = logging.getLogger('serializer')
logger.setLevel(logging.WARN)


class Serializer(object):
    """
    All serialization logic is implemented here
    """
    simple_types = (int, str, float, bytes, bool, type(None))  # Types that do nod need any serialization logic

    def __init__(self, **kwargs):
        """
        :date_format: str Babel-format
        :datetime_format: str Babel-format
        :tzinfo: datetime.tzinfo
        """
        self.opts = kwargs
        self.schema = None

    def __call__(self, value, only=(), extend=()):
        """
        Serialization starts here
        :param value: Value tu serialize
        :param only: Exclusive schema of serialization
        :param extend: Rules that extend default schema
        :return: object: JSON-compatible object
        """
        self.schema = Schema(only=only, extend=extend)

        logger.info(f'Call serializer for type:{get_type(value)}')
        if self.is_valid_callable(value):
            value = value()

        if isinstance(value, self.simple_types):
            return value

        elif isinstance(value, time):  # Should be always before datetime
            return self.serialize_time(value)

        elif isinstance(value, datetime):
            return self.serialize_datetime(value)

        elif isinstance(value, date):
            return self.serialize_date(value)

        elif isinstance(value, dict):
            return self.serialize_dict(value)

        elif isinstance(value, Iterable):
            return self.serialize_iter(value)

        elif isinstance(value, SerializerMixin):
            self.schema.merge(
                only=value.serialize_only if self.schema.is_greedy else (),
                extend=value.serialize_rules if self.schema.is_greedy else ()
            )
            return self.serialize_model(value)

        else:
            raise IsNotSerializable('Malformed value')

    @staticmethod
    def is_valid_callable(func):
        """
        Determines objects that should be called before serialization
        :param func:
        :return: bool
        """
        if callable(func):
            i = inspect.getfullargspec(func)
            if i.args == ['self'] and isinstance(func, MethodType) and not any([i.varargs, i.varkw]):
                return True
            return not any([i.args, i.varargs, i.varkw])
        return False

    def fork(self, value, key=None):
        """
        Process data in a separate serializer
        :param value:
        :param key:
        :return: serialized value
        """
        if isinstance(value, self.simple_types):
            return value
        serializer = Serializer(**self.opts)
        kwargs = self.schema.fork(key=key)
        logger.info(f'Fork serializer for type:{get_type(value)} with kwargs:{kwargs}')
        return serializer(value, **kwargs)

    def serialize_datetime(self, value):
        """
        datetime.datetime serialization logic
        :param value:
        :return: serialized value
        """
        tz = self.opts.get('tzinfo')
        if tz:
            value = to_local_time(dt=value, tzinfo=tz)
        return format_dt(
            tpl=self.opts.get('datetime_format'),
            dt=value
        )

    def serialize_date(self, value):
        """
        datetime.date serialization logic
        :param value:
        :return: serialized value
        """
        tz = self.opts.get('tzinfo')
        if tz:
            value = to_local_time(dt=value, tzinfo=tz)
        return format_dt(
            tpl=self.opts.get('date_format'),
            dt=value
        )

    def serialize_time(self, value):
        """
        datetime.time serialization logic
        :param value:
        :return: serialized value
        """
        return format_dt(
            tpl=self.opts.get('time_format'),
            dt=value
        )

    def serialize_iter(self, value):
        """
        Serialization logic for any iterable object
        :param value:
        :return: list
        """
        res = []
        for v in value:
            try:
                res.append(self.fork(value=v))
            except IsNotSerializable:
                logger.warning(f'Can not serialize type:{get_type(v)}')
                continue
        return res

    def serialize_dict(self, value):
        """
        Serialization logic for any dict
        :param value:
        :return: dict
        """
        res = {}
        for k, v in value.items():
            if self.schema.is_valid(k):
                logger.info(f'Serialize key:{k} type:{get_type(v)} of dict')
                res[k] = self.fork(key=k, value=v)
            else:
                logger.info(f'Skip key:{k} of dict')
        return res

    def serialize_model(self, value):
        """
        Serialization logic for instances of SerializerMixin
        :param value:
        :return: dict
        """
        res = {}
        # Check not negative keys from schema
        keys = self.schema.get_heads()
        # And model's keys
        keys.update(set(value.serializable_keys))
        for k in keys:
            if self.schema.is_valid(k):
                v = getattr(value, k)
                logger.info(f'Serialize key:{k} type:{get_type(v)} model:{get_type(value)}')
                res[k] = self.fork(key=k, value=v)
            else:
                logger.info(f'Skip key:{k} of model:{get_type(value)}')
        return res


class IsNotSerializable(Exception):
    pass


class SerializerMixin(object):
    """
    Mixin for retrieving public fields of sqlAlchemy-model in json-compatible format with no pain
    Can be inherited to redefine get_tzinfo callback, datetime formats or to add some extra serialization logic
    """

    # Default exclusive schema.
    # If left blank, serializer becomes greedy and takes all SQLAlchemy-model's attributes
    serialize_only = ()

    # Additions to default schema. Can include negative rules
    serialize_rules = ()

    date_format = '%Y-%m-%d'
    datetime_format = '%Y-%m-%d %H:%M'
    time_format = '%H:%M'

    def get_tzinfo(self):
        """
        Callback to make serializer aware of user's timezone. Should be redefined if needed
        :return: datetime.tzinfo
        """
        return None

    @property
    def serializable_keys(self):
        """
        :return: set of keys available for serialization
        """
        return {a.key for a in sql_inspect(self).mapper.attrs}

    def to_dict(self, only=(), rules=(), date_format=None, datetime_format=None, time_format=None, tzinfo=None):
        """
        Returns SQLAlchemy model's data in JSON compatible format

        For details about datetime formats follow:
        https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior

        :param only: exclusive schema to replace default one (always have higher priority than rules)
        :param rules: schema to extend default one or schema defined in "only"
        :param date_format: str
        :param datetime_format: str
        :param time_format: str
        :param tzinfo: datetime.tzinfo converts datetimes to local user timezone
        :return: data: dict
        """
        s = Serializer(
            date_format=date_format or self.date_format,
            datetime_format=datetime_format or self.datetime_format,
            time_format=time_format or self.time_format,
            tzinfo=tzinfo
        )
        return s(self, only=only, extend=rules)
