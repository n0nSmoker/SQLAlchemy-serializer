from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
import logging
import inspect

try:
    # Python 3
    from collections.abc import Iterable
except ImportError:
    # Python 2.7
    from collections import Iterable

from types import MethodType

from sqlalchemy import inspect as sql_inspect

from .lib.utils import get_type
from .lib.timezones import to_local_time, format_dt
from .lib.rules import Schema


logger = logging.getLogger('serializer')
logger.setLevel(level="WARN")


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

    # Extra serialising functions
    serialize_types = ()

    date_format = '%Y-%m-%d'
    datetime_format = '%Y-%m-%d %H:%M'
    time_format = '%H:%M'
    decimal_format = '{}'

    def get_tzinfo(self):
        """
        Callback to make serializer aware of user's timezone. Should be redefined if needed
        Example:
            return pytz.timezone('Asia/Krasnoyarsk')

        :return: datetime.tzinfo
        """
        return None

    @property
    def serializable_keys(self):
        """
        :return: set of keys available for serialization
        """
        return {a.key for a in sql_inspect(self).mapper.attrs}

    def to_dict(self, only=(), rules=(),
                date_format=None, datetime_format=None, time_format=None, tzinfo=None,
                decimal_format=None, serialize_types=None):
        """
        Returns SQLAlchemy model's data in JSON compatible format

        For details about datetime formats follow:
        https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior

        :param only: exclusive schema to replace default one (always have higher priority than rules)
        :param rules: schema to extend default one or schema defined in "only"
        :param date_format: str
        :param datetime_format: str
        :param time_format: str
        :param decimal_format: str
        :param serialize_types:
        :param tzinfo: datetime.tzinfo converts datetimes to local user timezone
        :return: data: dict
        """
        s = Serializer(
            date_format=date_format or self.date_format,
            datetime_format=datetime_format or self.datetime_format,
            time_format=time_format or self.time_format,
            decimal_format=decimal_format or self.decimal_format,
            tzinfo=tzinfo or self.get_tzinfo(),
            serialize_types=serialize_types or self.serialize_types
        )
        return s(self, only=only, extend=rules)


class Serializer(object):
    """
    All serialization logic is implemented here
    """
    simple_types = (int, str, float, bool, type(None))  # Types that do nod need any serialization logic
    complex_types = (Iterable, dict, SerializerMixin)

    def __init__(self, **kwargs):
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

        logger.info('Call serializer for type:%s', get_type(value))
        return self.serialize(value)

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
        if isinstance(value, self.simple_types) or not isinstance(value, self.complex_types):
            return self.serialize(value)

        serializer = Serializer(**self.opts)
        kwargs = self.schema.fork(key=key)
        logger.info('Fork serializer for type:%s with kwargs:%s', get_type(value), kwargs)
        return serializer(value, **kwargs)

    def serialize(self, value):
        if self.is_valid_callable(value):
            value = value()

        extra_serialization_types = self.opts.get('serialize_types', ())
        serialize_types = (
            *extra_serialization_types,
            (self.simple_types, lambda x: x),  # Should be checked before any other type
            (bytes, lambda x: x.decode()),
            (time, self.serialize_time),  # Should be checked before datetime
            (datetime, self.serialize_datetime),
            (date, self.serialize_date),
            (Decimal, self.serialize_decimal),
            (dict, self.serialize_dict),  # Should be checked before Iterable
            (Iterable, self.serialize_iter),
            (Enum, lambda x: value.value),
            (SerializerMixin, self.serialize_model),
        )
        for types, callback in serialize_types:
            if isinstance(value, types):
                return callback(value)
        raise IsNotSerializable(f'Unserializable type:{type(value)} value:{value}')

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

    def serialize_decimal(self, value):
        """
        decimal serialization logic
        :param value:
        :return: serialized value
        """
        f = self.opts.get('decimal_format')
        return f.format(value)

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
                logger.warning('Can not serialize type:%s', get_type(v))
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
                logger.info('Serialize key:%s type:%s of dict', k, get_type(v))
                res[k] = self.fork(key=k, value=v)
            else:
                logger.info('Skip key:%s of dict', k)
        return res

    def serialize_model(self, value):
        """
        Serialization logic for instances of SerializerMixin
        :param value:
        :return: dict
        """
        if self.schema.is_greedy:
            self.schema.merge(
                only=value.serialize_only,
                extend=value.serialize_rules
            )

        res = {}
        # Check not negative keys from schema
        keys = self.schema.get_heads()
        # And model's keys
        keys.update(set(value.serializable_keys))
        for k in keys:
            if self.schema.is_valid(k):
                v = getattr(value, k)
                logger.info('Serialize key:%s type:%s model:%s', k, get_type(v), get_type(value))
                res[k] = self.fork(key=k, value=v)
            else:
                logger.info('Skip key:%s of model:%s', k, get_type(value))
        return res


class IsNotSerializable(Exception):
    pass
