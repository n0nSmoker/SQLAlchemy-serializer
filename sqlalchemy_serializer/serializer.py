from datetime import datetime, date, time
import logging
import inspect

from collections import Iterable
from types import MethodType

from sqlalchemy import inspect as sql_inspect

from .lib.utils import get_type
from .lib.timezones import to_local_time, format_dt


logger = logging.getLogger('serializer')
logger.setLevel(logging.WARN)


DELIM = '.'      # Delimiter to separate nested rules
NEGATION = '-'   # Prefix for negative rules


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


class Schema(object):
    """
    Storage for serialization rules
    """
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
        logger.info(f'Init schema is_greedy:{self.is_greedy} rules:{rules}')
        self.update_tree(rules)

    def __repr__(self):
        schema = self.fork()
        return f'Schema(is_greedy={self.is_greedy}, only={schema["only"]}, extend={schema["extend"]})'

    def is_valid(self, key):
        """
        Turns key into a rule and checks that value of this key needs to be serialized
        :param key:
        :return:
        """
        rule = self.tree.get(Rule.to_negative(key))
        if rule is not None and not rule:
            return False
        return key in self.tree or self.is_greedy

    def update_tree(self, rules):
        """
        Safely updates tree with new rules
        :param rules:
        :return:
        """
        # Avoid useless logging
        if not rules:
            return

        logger.info(f'Update schema with rules:{rules}')
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
        # logger.info(f'Got tree:{self.tree}')

    def get_rules(self, key=None):
        rules = set()
        if key:
            for rule in self.tree.get(key, []):
                if rule:
                    rules.add(rule)
            for rule in self.tree.get(Rule.to_negative(key), []):
                assert rule, f'Key:{Rule.to_negative(key)} has empty branch of rules'
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
        """
        Returns top-level non-negative keys
        :return: set
        """
        return {k.text for k in self.tree.keys() if not k.is_negative}

    def fork(self, key=None):
        """
        Returns a branch of schema rules for exact key
        :param key:
        :return: dict(only, extend)
        """
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
        Merges new schema into existing one
        :param only:
        :param extend:
        :return:
        """
        if any([only, extend]):
            res = set()
            if only:
                self.is_greedy = False
            logger.info(f'Merge rules into schema only:{only} extend:{extend}')
            for r in only + extend:
                rule = Rule(text=r)
                head, tail = rule.divide()
                branch = self.tree.get(head.to_opposite(), [])
                if tail and tail.to_opposite() in branch:
                    logger.info(f'Can not merge rule:{rule}, found opposite one:{tail.to_opposite()}')
                    continue
                res.add(rule)
            self.update_tree(res)


class Rule(object):
    def __init__(self, text):
        assert isinstance(text, str), f'Text in rule should be a string, got:{get_type(text)}'
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
        return f'Rule({self.text})'

    @classmethod
    def to_list(cls, string):
        """
        :param string:  "-prop1.prop2"
        :return: list: ['-prop1', 'prop2']
        """
        return string.split(DELIM)

    @classmethod
    def to_string(cls, chain):
        """
        :param chain: list | tuple ['-prop1', 'prop2']
        :return: str: "-prop1.prop2"
        """
        return DELIM.join(chain)

    @classmethod
    def to_negative(cls, string):
        """
        :param string: "prop1.prop2"
        :return: str: "-prop1.prop2"
        """
        return '%s%s' % (NEGATION, string)

    @classmethod
    def to_positive(cls, string):
        """
        :param string: "-prop1.prop2"
        :return: str: "prop1.prop2"
        """
        return string[len(NEGATION):]

    @property
    def is_negative(self):
        """
        Checks if rule is negation
        :return: bool
        """
        return self.text.startswith(NEGATION)

    def negate(self):
        """
        Turns rule into negative one
        :return: Rule
        """
        if not self.is_negative:
            return Rule(text=Rule.to_negative(self.text))
        return Rule(text=self.text)

    def admit(self):
        """
        Turns rule into positive one
        :return: Rule
        """
        if self.is_negative:
            return Rule(text=Rule.to_positive(self.text))
        return Rule(text=self.text)

    def divide(self):
        """
        Splits rule into two strings (top-level key and all other nested ones)
        :return: tuple
        """
        head, *tail = Rule.to_list(self.text)
        logger.info(f'Split {self.text} into {head} and {tail}')
        head = Rule(head)
        if tail:
            tail = Rule(Rule.to_string(tail))
        if head.is_negative and tail:
            tail = tail.negate()
        return head, tail

    def concat(self, rule):
        """
        Adds rule at the end of current one
        :param rule:
        :return: Rule
        """
        assert isinstance(rule, Rule), 'Argument is not an instance of Rule class'
        rule = rule.admit()
        return Rule(text=Rule.to_string([self.text, rule.text]))

    def to_opposite(self):
        """
        Turns positive rule into negative one and vice versa
        :return: Rule
        """
        if self.is_negative:
            return self.admit()
        return self.negate()


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

