from datetime import datetime, date
import logging
import inspect

from collections import Iterable
from sqlalchemy import inspect as sql_inspect
from lib.timezones import to_local_time, format_date, format_datetime


logger = logging.getLogger('serializer')
logger.setLevel(logging.INFO)


class Serializer(object):
    _WILDCARD = '*'
    _DELIM = '.'
    _NEGATION = '-'
    simple_types = (int, str, float, bytes, bool, type(None))
    is_greedy = True

    def __init__(self, **kwargs):
        """
        :date_format: str Babel-format
        :datetime_format: str Babel-format
        :to_user_tz: bool
        """
        self.kwargs = kwargs
        self.schema = None
        self._keys = {}

    def __call__(self, value, schema=(), extend=()):
        if schema:
            # Use user defined schema only
            self.is_greedy = False
        self.schema = self.merge_schemas(schema, extend)

        logger.info('Called schema:%s extend:%s value:%s' % (self.schema, extend, value))
        if self.is_valid_callable(value):
            value = value()

        if isinstance(value, self.simple_types):
            return value

        elif isinstance(value, datetime):
            return self.serialize_datetime(value)

        elif isinstance(value, date):
            return self.serialize_date(value)

        elif isinstance(value, Iterable):
            return self.serialize_iter(value)

        elif isinstance(value, SerializerMixin):
            self._set_keys(
                self.merge_schemas(value.__schema__, self.schema)
            )
            return self.serialize_model(value)

        elif isinstance(value, dict):
            self._set_keys(self.schema)
            return self.serialize_dict(value)

        else:
            raise IsNotSerializable('Malformed value')

    @property
    def to_user_tz(self):
        return bool(self.kwargs.get('to_user_tz', False))

    @property
    def datetime_format(self):
        return self.kwargs.get('datetime_format') or '%Y-%m-%d %H:%M'

    @property
    def date_format(self):
        return self.kwargs.get('date_format') or '%Y-%m-%d'

    @staticmethod
    def is_valid_callable(func):
        if callable(func):
            i = inspect.getfullargspec(func)
            return not any([i.args, i.varargs, i.varkw])
        return False

    def _fork(self, value, key=None):
        """
        Process data in a separate serializer
        :param value:
        :param key:
        :return: serialized value
        """
        if isinstance(value, self.simple_types):
            return value
        serializer = Serializer(**self.kwargs)
        prop_name = 'extend' if self.is_greedy else 'schema'
        schema = self._get_sub_schema(key=key) if key else self.schema
        return serializer(value, **{prop_name: schema})

    def _negate(self, key):
        return '%s%s' % (self._NEGATION, key)

    def _is_negation(self, key):
        return key.startswith(self._NEGATION)

    def _admit(self, key):
        if self._is_negation(key):
            return key[len(self._NEGATION):]
        return key

    def _is_valid(self, key):
        if self._negate(key) in self._keys:
            if not self._keys[self._negate(key)]:  # If tail is empty
                return False
        if self._WILDCARD in self._keys:
            return True
        return key in self._keys or self.is_greedy

    def _to_list(self, key):
        """
        :param key:  "-prop1.prop2.*"
        :return: list: ['-prop1', 'prop2', '*']
        """
        return key.split(self._DELIM)

    def _to_string(self, key):
        """
        :param key: ['-prop1', 'prop2', '*']
        :return: str: "-prop1.prop2.*"
        """
        return self._DELIM.join(key)

    def _set_keys(self, keys):
        for k in keys:
            head, *tail = self._to_list(k)
            if head in self._keys:
                if tail:
                    self._keys[head].append(tail)
            else:
                self._keys[head] = [tail] if tail else []
        logger.info('Set keys:%s' % self._keys)

    def _get_sub_schema(self, key):
        keys = []
        for k in self._keys.get(key, []):
            if k:
                keys.append(k)
        for k in self._keys.get(self._negate(key), []):
            assert k, 'key:%s has empty subkeys' % self._negate(key)
            # move negation mark to the next element
            k[0] = self._negate(k[0])
            keys.append(k)

        # Keys are lists but we need string keys in schema
        return [self._to_string(k) for k in keys]

    def merge_schemas(self, *args):
        """
        Merges lists of string-keys, priority grows from left to right
        :param args: tuple of lists of keys
        :return: list
        """
        logger.info('Merge schemas:%s' % str(args))
        lists = list(args)
        lists.reverse()
        res = set()
        while lists:
            keys = lists.pop()
            logger.info('Check schema:%s' % str(keys))
            for k in keys:
                if self._is_negation(k):
                    if self._admit(k) in res:
                        logger.info('Remove key:%s' % self._admit(k))
                        res.remove(self._admit(k))
                else:
                    if self._negate(k) in res:
                        logger.info('Remove key:%s' % self._negate(k))
                        res.remove(self._negate(k))
                logger.info('Add key:%s' % k)
                res.add(k)
        return res

    def serialize_datetime(self, value):
        if self.to_user_tz:
            value = to_local_time(value)
            return format_datetime(value, self.datetime_format, rebase=False)
        return value.strftime(self.datetime_format)

    def serialize_date(self, value):
        if self.to_user_tz:
            return format_date(value, self.date_format, rebase=False)
        return value.strftime(self.date_format)

    def serialize_iter(self, value):
        res = []
        for v in value:
            try:
                res.append(self._fork(value=v))
            except IsNotSerializable:
                continue
        return res

    def serialize_dict(self, value):
        res = {}
        for k, v in value.items():
            if self._is_valid(k):
                logger.info('Serialize key:%s' % k)
                res[k] = self._fork(key=k, value=v)
            else:
                logger.info('Skipped key:%s' % k)
        return res

    def serialize_model(self, value):
        res = {}
        # Check model keys and not negative keys from schema as well
        keys = {k for k in self._keys.keys() if not self._is_negation(k)}
        for k in value.serializable_keys.union(keys):
            if self._is_valid(k):
                v = getattr(value, k)
                res[k] = self._fork(key=k, value=v)
            else:
                logger.info('Skipped KEY:%s' % k)
        return res


class IsNotSerializable(Exception):
    pass


class SerializerMixin(object):
    """Mixin for retrieving public fields of sqlAlchemy-model in json-compatible format"""
    __schema__ = ()  # default schema, define it in your model

    @property
    def serializable_keys(self):
        """
        :return: set of keys
        """
        return {a.key for a in sql_inspect(self).mapper.attrs}

    def to_dict(self, schema=(), extend=(), date_format=None, datetime_format=None, to_user_tz=False):
        r"""
        Returns SQLAlchemy model's data in JSON compatible format\n

        :param schema: iterable schema to replace existing one
        :param extend: iterable schema to extend existing one
        :param date_format: str in Babel format
        :param datetime_format: str in Babel format
        :param to_user_tz: whether or not convert datetimes to local user timezone (Babel)

        :return: data: dict
        """
        s = Serializer(
            date_format=date_format,
            datetime_format=datetime_format,
            to_user_tz=to_user_tz
        )
        return s(self, schema=schema, extend=extend)

