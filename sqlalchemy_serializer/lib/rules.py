import logging
from .utils import get_type


logger = logging.getLogger('serializer')

DELIM = '.'      # Delimiter to separate nested rules
NEGATION = '-'   # Prefix for negative rules


class Schema(object):
    """
    Storage for serialization rules
    """
    def __init__(self, only=(), extend=()):
        """
        Generate tree of rules here
        :param only: Exclusive schema of serialization
        :param extend: Rules that extend default schema
        """
        only = set(only)
        extend = set(extend)
        self.tree = {}

        # Rules from ONLY param
        rules = {Rule(text=r) for r in only}

        # Set is_greedy if there were non negative rules in ONLY param
        self.is_greedy = not bool(rules)

        # Add extra rules
        for r in extend:
            rules.add(Rule(text=r))

        logger.info('Init schema is_greedy:%s rules:%s', self.is_greedy, rules)
        self.update_tree(rules)

    def __repr__(self):
        """
        Brief string representation mostly for nice logging
        :return: str
        """
        schema = self.fork()
        return f'Schema(is_greedy={self.is_greedy}, only={schema["only"]}, extend={schema["extend"]})'

    def is_valid(self, key):
        """
        Turns key into a rule and checks that value of this key needs to be serialized
        :param key:
        :return: bool
        """
        rule = self.tree.get(Rule.to_negative(key))
        if rule is not None and not rule:  # Negative rule got no ancestors
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

        logger.info('Update schema with rules:%s', rules)
        for rule in rules:
            head, tail = rule.divide()

            # Look for opposite rules and if so ignore the rule
            if head.to_opposite() in self.tree:
                if not tail:
                    if not self.tree[head.to_opposite()]:
                        continue
                elif tail.to_opposite() in self.tree[head.to_opposite()]:
                    continue

            if head in self.tree:
                if tail:
                    self.tree[head].add(tail)
            else:
                self.tree[head] = {tail} if tail else set()
        # logger.info(f'Got tree:{self.tree}')

    def get_rules(self, key=None):
        """
        Returns branch for exact key or the whole tree if key is None
        :param key: str
        :return: set of rules
        """
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
        Returns only and extend params for exact key to use them in serializer
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
            logger.info('Merge rules into schema only:%s extend:%s', only, extend)
            for r in only + extend:
                rule = Rule(text=r)
                head, tail = rule.divide()
                branch = self.tree.get(head.to_opposite(), [])
                if tail and tail.to_opposite() in branch:
                    logger.info('Can not merge rule:%s, found opposite one:%s', rule, tail.to_opposite())
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
        logger.info('Split %s into %s and %s', self.text, head, tail)
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

