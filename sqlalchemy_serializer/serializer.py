import uuid
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
import logging
import inspect
from collections import namedtuple
from collections.abc import Iterable
from types import MethodType
import typing as t

from sqlalchemy_serializer.lib.fields import get_serializable_keys

from .lib.schema import Schema
from .lib import serializable


logger = logging.getLogger('serializer')
logger.setLevel(level="WARN")


class SerializerMixin:
    """
    Mixin for retrieving public fields of sqlAlchemy-model in json-compatible format with no pain
    Can be inherited to redefine get_tzinfo callback, datetime formats or to add some extra serialization logic
    """

    # Default exclusive schema.
    # If left blank, serializer becomes greedy and takes all SQLAlchemy-model's attributes
    serialize_only: tuple = ()

    # Additions to default schema. Can include negative rules
    serialize_rules: tuple = ()

    # Extra serialising functions
    serialize_types: tuple = ()

    date_format = '%Y-%m-%d'
    datetime_format = '%Y-%m-%d %H:%M:%S'
    time_format = '%H:%M'
    decimal_format = '{}'

    # Custom list of fields to serialize in this model
    serializable_keys: tuple = ()

    # Serialize fields of the model defined as @property automatically
    auto_serialize_properties: bool = False

    def get_tzinfo(self):
        """
        Callback to make serializer aware of user's timezone. Should be redefined if needed
        Example:
            return pytz.timezone('Asia/Krasnoyarsk')

        :return: datetime.tzinfo
        """
        return None

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


Options = namedtuple('Options', 'date_format datetime_format time_format decimal_format tzinfo serialize_types')


class Serializer:
    atomic_types = (int, str, float, bool, type(None))  # Types that do nod need any serialization logic

    def __init__(self, **kwargs):
        self.opts = Options(**kwargs)  # Serializer o
        self.schema = Schema()

        self.serialize_types = (
            *(self.opts.serialize_types or ()),
            (self.atomic_types, lambda x: x),  # Should be checked before any other type
            (bytes, serializable.Bytes()),
            (uuid.UUID, serializable.UUID()),
            (time, serializable.Time(str_format=self.opts.time_format)),  # Should be checked before datetime
            (datetime, serializable.DateTime(str_format=self.opts.datetime_format, tzinfo=self.opts.tzinfo)),
            (date, serializable.Date(str_format=self.opts.date_format)),
            (Decimal, serializable.Decimal(str_format=self.opts.decimal_format)),
            (dict, self.serialize_dict),  # Should be checked before Iterable
            (Iterable, self.serialize_iter),
            (Enum, serializable.Enum()),
            (SerializerMixin, self.serialize_model),
        )

    def __call__(self, value, only=(), extend=()):
        """
        Serialization starts here
        :param value: Value to serialize
        :param only: Exclusive schema of serialization
        :param extend: Rules that extend default schema
        :return: object: JSON-compatible object
        """
        self.schema.update(only=only, extend=extend)

        logger.debug('Call serializer for type:%s', get_type(value))
        return self.serialize(value)

    @staticmethod
    def is_valid_callable(func) -> bool:
        """
        Determines objects that should be called before serialization
        """
        if callable(func):
            i = inspect.getfullargspec(func)
            if i.args == ['self'] and isinstance(func, MethodType) and not any([i.varargs, i.varkw]):
                return True
            return not any([i.args, i.varargs, i.varkw])
        return False

    def is_forkable(self, value):
        """
        Determines if object should be processed in a separate serializer
        """
        return not isinstance(value, str) and isinstance(value, (Iterable, dict, SerializerMixin))

    def fork(self, value, key: t.Optional[str] = None):
        """
        Process data in a separate serializer
        :return: serialized value
        """
        if not self.is_forkable(value):
            return self.serialize(value)

        serializer = Serializer(**self.opts._asdict())
        if key is None:
            serializer.schema = self.schema
        else:
            serializer.schema = self.schema.fork(key=key)

        logger.debug('Fork serializer for type:%s', get_type(value))
        return serializer(value)

    def serialize(self, value):
        if self.is_valid_callable(value):
            value = value()

        for types, callback in self.serialize_types:
            if isinstance(value, types):
                return callback(value)
        raise IsNotSerializable(f'Unserializable type:{type(value)} value:{value}')

    def serialize_iter(self, value: Iterable) -> list:
        res = []
        for v in value:
            try:
                res.append(self.fork(value=v))
            except IsNotSerializable:
                logger.warning('Can not serialize type:%s', get_type(v))
                continue
        return res

    def serialize_dict(self, value: dict) -> dict:
        res = {}
        for k, v in value.items():
            if self.schema.is_included(k):  # TODO: Skip check if is NOT greedy
                logger.debug('Serialize key:%s type:%s of dict', k, get_type(v))
                res[k] = self.fork(key=k, value=v)
            else:
                logger.debug('Skip key:%s of dict', k)
        return res

    def serialize_model(self, value) -> dict:
        self.schema.update(
            only=value.serialize_only,
            extend=value.serialize_rules
        )

        res = {}
        keys = self.schema.keys
        if self.schema.is_greedy:
            keys.update(get_serializable_keys(value))

        for k in keys:
            if self.schema.is_included(key=k):  # TODO: Skip check if is NOT greedy
                v = getattr(value, k)
                logger.debug('Serialize key:%s type:%s model:%s', k, get_type(v), get_type(value))
                res[k] = self.fork(key=k, value=v)
            else:
                logger.debug('Skip key:%s of model:%s', k, get_type(value))
        return res


class IsNotSerializable(Exception):
    pass


def get_type(value) -> str:
    return type(value).__name__


def serialize_collection(iterable: t.Iterable, *args, **kwargs) -> list:
    return [item.to_dict(*args, **kwargs) for item in iterable]
