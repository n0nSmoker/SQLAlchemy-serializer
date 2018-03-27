from datetime import datetime, date
import logging
import inspect

from collections import Iterable
from types import MethodType

from sqlalchemy import inspect as sql_inspect
from .lib.timezones import to_local_time, format_date, format_datetime


logger = logging.getLogger('serializer')
logger.setLevel(logging.WARN)


class Serializer(object):
    simple_types = (int, str, float, bytes, bool, type(None))

    def __init__(self, **kwargs):
        """
        :date_format: str Babel-format
        :datetime_format: str Babel-format
        :to_user_tz: bool
        """
        self.kwargs = kwargs
        self.schema = None

    def __call__(self, value, only=(), extend=()):
        self.schema = Schema(only=only, extend=extend)

        logger.info('Called %s value:%s' % (self.schema, value))
        if self.is_valid_callable(value):
            value = value()

        if isinstance(value, self.simple_types):
            return value

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
                only=value.__schema_only__ if self.schema.is_greedy else (),
                extend=value.__schema_extend__ if self.schema.is_greedy else ()
            )
            return self.serialize_model(value)

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
            if i.args == ['self'] and isinstance(func, MethodType) and not any([i.varargs, i.varkw]):
                return True
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
        kwargs = self.schema.fork(key=key)
        logger.info('Fork serializer kwargs:%s, value=%s' % (str(kwargs), value))
        return serializer(value, **kwargs)

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
            if self.schema.is_valid(k):
                logger.info('Serialize key:%s' % k)
                res[k] = self._fork(key=k, value=v)
            else:
                logger.info('Skipped key:%s' % k)
        return res

    def serialize_model(self, value):
        res = {}
        # Check not negative keys from schema
        keys = self.schema.get_heads()
        # And model's keys
        keys.update(set(value.serializable_keys))
        for k in keys:
            if self.schema.is_valid(k):
                v = getattr(value, k)
                logger.info('Serialize key:%s' % k)
                res[k] = self._fork(key=k, value=v)
            else:
                logger.info('Skipped KEY:%s' % k)
        return res


class IsNotSerializable(Exception):
    pass


class Schema(object):
    _DELIM = '.'
    _NEGATION = '-'

    def __init__(self, only=(), extend=()):
        only = set(only)
        extend = set(extend)
        rules = set()
        neg_rules = set()
        self.tree = {}
        for r in only:
            rule = Rule(text=r)
            # Negative rules should be removed from only-container
            if rule.is_negative:
                neg_rules.add(r)
            rules.add(rule)

        for r in extend:
            rules.add(Rule(text=r))

        self.is_greedy = not bool(only - neg_rules)
        logger.info('Set schema is_greedy:%s, rules:%s' % (self.is_greedy, rules))
        self.update_tree(rules)

    def __repr__(self):
        return 'Schema(is_greedy=%s, only=%s, extend=%s)' % (
            self.is_greedy, str(self.fork()['only']), str(self.fork()['extend'])
        )

    def is_valid(self, key):
        rule = self.tree.get(Rule._to_negative(key))
        if rule is not None and not rule:
            return False
        return key in self.tree or self.is_greedy

    def update_tree(self, rules):
        logger.info('Update schema with rules:%s' % rules)
        for rule in rules:
            head, tail = rule.divide()

            # Look for opposite rules
            if head.to_opposite() in self.tree:
                if not tail:
                    if not self.tree[head.to_opposite()]:
                        # ignore rule because there's already an opposite one
                        continue
                elif tail.to_opposite() in self.tree[head.to_opposite()]:
                    # ignore rule because there's already an opposite one
                    continue

            if head in self.tree:
                if tail:
                    self.tree[head].add(tail)
            else:
                self.tree[head] = {tail} if tail else set()
        logger.info('Set tree:%s' % self.tree)

    def get_rules(self, key=None):
        rules = set()
        if key:
            for rule in self.tree.get(key, []):
                if rule:
                    rules.add(rule)
            for rule in self.tree.get(Rule._to_negative(key), []):
                assert rule, 'key:%s has empty branch of rules' % Rule._to_negative(key)
                rules.add(rule)
        else:
            for head, bunch in self.tree.items():
                if bunch:
                    for rule in bunch:
                        rules.add(head.concat(rule))
                else:
                    rules.add(head)
        return rules

    def get_heads(self):
        return {k.text for k in self.tree.keys() if not k.is_negative}

    def fork(self, key=None):
        only = set()
        extend = set()
        for rule in self.get_rules(key=key):
            if rule.is_negative or self.is_greedy:
                extend.add(rule.text)
            else:
                only.add(rule.text)
        return dict(
            only=only,
            extend=extend
        )

    def merge(self, only=(), extend=()):
        """
        Merges new rules into schema
        :param only:
        :param extend:
        :return:
        """
        res = set()
        if only:
            self.is_greedy = False
        logger.info('Merge rules into schema only:%s extend:%s' % (only, extend))
        for r in only + extend:
            rule = Rule(text=r)
            head, tail = rule.divide()
            branch = self.tree.get(head.to_opposite(), [])
            if tail and tail.to_opposite() in branch:
                logger.info(
                    'Do not merge rule:%s, found opposite one:%s in tree' %
                    (rule, tail.to_opposite())
                )
                continue
            res.add(rule)
        self.update_tree(res)


class Rule(object):
    _DELIM = '.'
    _NEGATION = '-'

    def __init__(self, text):
        assert isinstance(text, str), 'Text in rule should be a string, got:%s' % type(text)
        assert text, 'Can not create Rule without text'
        self.text = text

    def __lt__(self, other):
        return self.text < other

    def __le__(self, other):
        return self.text <= other

    def __eq__(self, other):
        return self.text == other

    def __ne__(self, other):
        return self.text != other

    def __gt__(self, other):
        return self.text > other

    def __ge__(self, other):
        return self.text >= other

    def __hash__(self):
        return hash(self.text)

    def __repr__(self):
        return 'Rule(%s)' % self.text

    @classmethod
    def _to_list(cls, string):
        """
        :param string:  "-prop1.prop2"
        :return: list: ['-prop1', 'prop2']
        """
        return string.split(cls._DELIM)

    @classmethod
    def _to_string(cls, chain):
        """
        :param chain: list | tuple ['-prop1', 'prop2']
        :return: str: "-prop1.prop2"
        """
        return cls._DELIM.join(chain)

    @classmethod
    def _to_negative(cls, string):
        """
        :param string: "prop1.prop2"
        :return: str: "-prop1.prop2"
        """
        return '%s%s' % (cls._NEGATION, string)

    @classmethod
    def _to_positive(cls, string):
        """
        :param string: "-prop1.prop2"
        :return: str: "prop1.prop2"
        """
        return string[len(cls._NEGATION):]

    @property
    def is_negative(self):
        return self.text.startswith(self._NEGATION)

    def negate(self):
        if not self.is_negative:
            return Rule(text=Rule._to_negative(self.text))
        return Rule(text=self.text)

    def admit(self):
        if self.is_negative:
            return Rule(text=Rule._to_positive(self.text))
        return Rule(text=self.text)

    def divide(self):
        head, *tail = Rule._to_list(self.text)
        logger.info('Split %s into %s and %s' % (self.text, head, tail))
        head = Rule(head)
        if tail:
            tail = Rule(Rule._to_string(tail))
        if head.is_negative and tail:
            tail = tail.negate()
        return head, tail

    def concat(self, rule):
        assert isinstance(rule, Rule), 'Argument is not an instance of Rule class'
        rule = rule.admit()
        return Rule(text=Rule._to_string([self.text, rule.text]))

    def to_opposite(self):
        if self.is_negative:
            return self.admit()
        return self.negate()


class SerializerMixin(object):
    """Mixin for retrieving public fields of sqlAlchemy-model in json-compatible format with no pain"""

    # Default exclusive schema.
    # If left blank, serializer become greedy and take all SQLAlchemy-model's attributes
    __schema_only__ = ()

    # Additions to default schema. Can include negative rules
    __schema_extend__ = ()

    @property
    def serializable_keys(self):
        """
        :return: set of keys
        """
        return {a.key for a in sql_inspect(self).mapper.attrs}

    def to_dict(self, only=(), extend=(), date_format=None, datetime_format=None, to_user_tz=False):
        r"""
        Returns SQLAlchemy model's data in JSON compatible format

        :param only: exclusive schema to replace default one
        :param extend: schema to extend default one or schema defined in "only"
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
        return s(self, only=only, extend=extend)

