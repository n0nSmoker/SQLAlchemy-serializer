import inspect
import logging
import math
import typing as t
import uuid
from collections import namedtuple
from collections.abc import Iterable
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from types import MethodType

from sqlalchemy_serializer.lib.fields import get_serializable_keys

from .lib import serializable
from .lib.schema import Schema

logger = logging.getLogger("serializer")
logger.setLevel(level="WARN")

SERIALIZER_DEFAULT_DATE_FORMAT = "%Y-%m-%d"
SERIALIZER_DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
SERIALIZER_DEFAULT_TIME_FORMAT = "%H:%M"
SERIALIZER_DEFAULT_DECIMAL_FORMAT = "{}"

# sentinel value for unspecified key since None and Ellipsis are valid keys
_UNSPECIFIED = object()


class SerializerMixin:
    """Mixin for retrieving public fields of SQLAlchemy-model in json-compatible format
    with no pain
    It can be inherited to redefine get_tzinfo callback, datetime formats or to add
    some extra serialization logic
    """

    # Default exclusive schema.
    # If left blank, serializer becomes greedy and takes all SQLAlchemy-model's attributes
    serialize_only: tuple = ()

    # Additions to default schema. Can include negative rules
    serialize_rules: tuple = ()

    # Extra serializing functions
    serialize_types: tuple = ()

    # Custom list of fields to serialize in this model
    serializable_keys: tuple = ()

    # Iterable of hashable values to exclude from serialized output
    exclude_values: Iterable = ()

    date_format = SERIALIZER_DEFAULT_DATE_FORMAT
    datetime_format = SERIALIZER_DEFAULT_DATETIME_FORMAT
    time_format = SERIALIZER_DEFAULT_TIME_FORMAT
    decimal_format = SERIALIZER_DEFAULT_DECIMAL_FORMAT

    # Serialize fields of the model defined as @property automatically
    auto_serialize_properties: bool = False

    # Maximum depth for relationship recursion (default: unlimited)
    max_serialization_depth: float = math.inf

    # Custom serializers per column name
    serialize_columns: dict = {}

    def get_tzinfo(self):
        """Callback to make serializer aware of user's timezone. Should be redefined if needed
        Example:
            return pytz.timezone('Africa/Abidjan')

        :return: datetime.tzinfo
        """
        return

    def to_dict(
        self,
        only=(),
        rules=(),
        date_format=None,
        datetime_format=None,
        time_format=None,
        tzinfo=None,
        decimal_format=None,
        serialize_types=None,
        exclude_values=None,
        max_serialization_depth=None,
        serialize_columns=None,
    ) -> dict:
        """Returns SQLAlchemy model's data in JSON compatible format

        For details about datetime formats follow:
        https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior

        :param only: exclusive schema to replace the default one
            always have higher priority than rules
        :param rules: schema to extend default one or schema defined in "only"
        :param date_format: str
        :param datetime_format: str
        :param time_format: str
        :param decimal_format: str
        :param serialize_types:
        :param tzinfo: datetime.tzinfo converts datetimes to local user timezone
        :param exclude_values: iterable of hashable values to exclude from serialized output
        :param max_serialization_depth: maximum depth for relationship recursion
            (default: unlimited)
        :param serialize_columns: dict mapping column names to custom serializer functions.
            Custom serializers replace normal serialization for matching columns.
        :return: data: dict
        """
        s = Serializer(
            date_format=date_format or self.date_format,
            datetime_format=datetime_format or self.datetime_format,
            time_format=time_format or self.time_format,
            decimal_format=decimal_format or self.decimal_format,
            tzinfo=tzinfo or self.get_tzinfo(),
            serialize_types=serialize_types or self.serialize_types,
            exclude_values=exclude_values or self.exclude_values,
            max_serialization_depth=(
                max_serialization_depth
                if max_serialization_depth is not None
                else self.max_serialization_depth
            ),
            serialize_columns=serialize_columns or self.serialize_columns,
        )
        return s(self, only=only, extend=rules)  # type: ignore


Options = namedtuple(
    "Options",
    "date_format datetime_format time_format decimal_format tzinfo serialize_types exclude_values max_serialization_depth serialize_columns",  # noqa: E501
)


class Serializer:
    # Types that do not need any serialization logic
    atomic_types = (
        int,
        str,
        float,
        bool,
        type(None),
    )

    def __init__(self, **kwargs):
        self.set_serialization_depth(0)
        # Provide defaults for Options if not specified
        exclude_values = kwargs.get("exclude_values")
        exclude_values_set = set(exclude_values) if exclude_values else None

        options_kwargs = {
            "date_format": kwargs.get("date_format", SERIALIZER_DEFAULT_DATE_FORMAT),
            "datetime_format": kwargs.get(
                "datetime_format", SERIALIZER_DEFAULT_DATETIME_FORMAT
            ),
            "time_format": kwargs.get("time_format", SERIALIZER_DEFAULT_TIME_FORMAT),
            "decimal_format": kwargs.get("decimal_format", SERIALIZER_DEFAULT_DECIMAL_FORMAT),
            "tzinfo": kwargs.get("tzinfo"),
            "serialize_types": kwargs.get("serialize_types", ()),
            "exclude_values": exclude_values_set,
            "max_serialization_depth": kwargs.get("max_serialization_depth", math.inf),
            "serialize_columns": kwargs.get("serialize_columns", {}),
        }
        self.set_options(Options(**options_kwargs))
        self.init_callbacks()

        self.schema = Schema()

    def __call__(self, value, only=(), extend=()):
        """Serialization starts here
        :param value: Value to serialize
        :param only: Exclusive schema of serialization
        :param extend: Rules that extend default schema
        :return: object: JSON-compatible object
        """
        self.schema.update(only=only, extend=extend)

        logger.debug("Call serializer for type:%s", get_type(value))
        return self.serialize(value)

    def set_serialization_depth(self, value: int):
        self.serialization_depth = value

    def set_options(self, opts: Options):
        self.opts = opts

    def should_exclude(self, value) -> bool:
        """Check if value should be excluded based on exclude_values"""
        if self.opts.exclude_values is None:
            return False
        try:
            # if value is not hashable, we cannot compare it with exclude_values
            hash(value)
        except TypeError:
            return False

        return value in self.opts.exclude_values

    def init_callbacks(self):
        """Initialize callbacks"""
        self.serialize_types = (
            *(self.opts.serialize_types or ()),
            (self.atomic_types, lambda x: x),  # Should be checked before any other type
            (bytes, serializable.Bytes()),
            (uuid.UUID, serializable.UUID()),
            (
                time,  # Should be checked before datetime
                serializable.Time(str_format=self.opts.time_format),
            ),
            (
                datetime,
                serializable.DateTime(
                    str_format=self.opts.datetime_format, tzinfo=self.opts.tzinfo
                ),
            ),
            (date, serializable.Date(str_format=self.opts.date_format)),
            (Decimal, serializable.Decimal(str_format=self.opts.decimal_format)),
            (dict, self.serialize_dict),  # Should be checked before Iterable
            (Iterable, self.serialize_iter),
            (Enum, serializable.Enum()),
            (SerializerMixin, self.serialize_model),
        )

    @staticmethod
    def is_valid_callable(func) -> bool:
        """Determines objects that should be called before serialization"""
        if not callable(func):
            return False

        i = inspect.getfullargspec(func)

        # Check for varargs/varkw
        # (methods with *args or **kwargs are not callable without args)
        if any([i.varargs, i.varkw]):
            return False

        # For methods: check if all args except 'self' have defaults
        if isinstance(func, MethodType):
            if not i.args or i.args[0] != "self":
                return False
            # All args except self must have defaults
            args_count = len(i.args) - 1
        else:
            # For functions: all args must have defaults
            args_count = len(i.args) if i.args else 0

        defaults_count = len(i.defaults) if i.defaults else 0
        return args_count == defaults_count

    def is_forkable(self, value):
        """Determines if object should be processed in a separate serializer"""
        return not isinstance(value, str) and isinstance(
            value, (Iterable, dict, SerializerMixin)
        )

    def fork(self, key: str) -> "Serializer":
        """Return new serializer for a key
        :return: serializer
        """
        serializer = Serializer(**self.opts._asdict())
        serializer.set_serialization_depth(self.serialization_depth + 1)
        serializer.schema = self.schema.fork(key=key)

        logger.debug("Fork serializer for key:%s", key)
        return serializer

    def serialize(self, value, key=_UNSPECIFIED):
        """Orchestrates the serialization process.

        Args:
            value: The value to be serialized.
            key: The key to be serialized.

        Returns:
            The serialized value.
        """
        if self.is_valid_callable(value):
            value = value()
            logger.debug("Process callable resulting type:%s", get_type(value))

        if not self.should_exclude(value):
            try:
                if key is not _UNSPECIFIED:  # since None and Ellipsis are valid keys
                    return self.serialize_with_fork(value=value, key=key)
                return self.apply_callback(value=value)

            except IsNotSerializable:
                logger.warning("Cannot serialize type:%s", get_type(value))

        logger.debug("Skip value:%s", value)
        return _UNSPECIFIED

    def apply_callback(self, value):
        """Apply a proper callback to serialize the value
        :return: serialized value
        :raises: IsNotSerializable
        """
        for types, callback in self.serialize_types:
            if isinstance(value, types):
                return callback(value)
        raise IsNotSerializable(f"Unserializable type:{get_type(value)} value:{value}")

    def serialize_with_fork(self, value, key):
        """Serialize value with a forked serializer"""
        # Check if there's a custom serializer for this column
        if self.opts.serialize_columns and key in self.opts.serialize_columns:
            custom_serializer = self.opts.serialize_columns[key]
            logger.debug("Apply custom serializer for key:%s", key)
            return custom_serializer(value)

        serializer = self
        if self.is_forkable(value):
            # Check depth limit before forking
            if self.serialization_depth >= self.opts.max_serialization_depth:
                logger.debug(
                    "Max serialization depth reached at depth:%s for key:%s",
                    self.serialization_depth,
                    key,
                )
                return _UNSPECIFIED
            serializer = self.fork(key=key)

        return serializer.apply_callback(value)

    def serialize_iter(self, value: Iterable) -> list:
        res = []
        for v in value:
            result = self.serialize(v)
            if result is not _UNSPECIFIED:
                res.append(result)
        return res

    def serialize_dict(self, value: dict) -> dict:
        res = {}
        for k, v in value.items():
            if self.schema.is_included(k):
                logger.debug("Serialize key:%s type:%s of dict", k, get_type(v))

                result = self.serialize(value=v, key=k)
                if result is not _UNSPECIFIED:
                    res[k] = result
            else:
                logger.debug("Skip key:%s of dict", k)
        return res

    def serialize_model(self, value) -> dict:
        self.schema.update(only=value.serialize_only, extend=value.serialize_rules)

        res = {}
        keys = self.schema.keys
        if self.schema.is_greedy:
            keys.update(get_serializable_keys(value))

        for k in keys:
            if self.schema.is_included(key=k):
                v = getattr(value, k)
                logger.debug(
                    "Serialize key:%s type:%s of model:%s",
                    k,
                    get_type(v),
                    get_type(value),
                )
                result = self.serialize(value=v, key=k)
                if result is not _UNSPECIFIED:
                    res[k] = result

            else:
                logger.debug("Skip key:%s of model:%s", k, get_type(value))
        return res


class IsNotSerializable(Exception):
    pass


def get_type(value) -> str:
    return type(value).__name__


def serialize_collection(iterable: t.Iterable, *args, **kwargs) -> list:
    return [item.to_dict(*args, **kwargs) for item in iterable]
