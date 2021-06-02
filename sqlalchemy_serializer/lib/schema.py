import logging
from collections import defaultdict


logger = logging.getLogger('serializer')


class Tree(defaultdict):
    def __init__(self, to_include=None, to_exclude=None, is_greedy=True, *args, **kwargs):
        super(Tree, self).__init__(*args, **kwargs)
        self.default_factory = Tree
        self.to_include = to_include
        self.to_exclude = to_exclude
        self.is_greedy = is_greedy

    def apply(self, node: 'Tree'):
        if self.is_greedy and not node.is_greedy:
            # Apply strictness to all subtrees
            # not included into the node
            for k, subtree in self.items():
                if k not in node.keys() and subtree:
                    subtree.to_strict()

        self.is_greedy = node.is_greedy and self.is_greedy

        if node.to_include is not None:
            self.to_include = node.to_include

        if node.to_exclude is not None:
            self.to_exclude = node.to_exclude

    def to_strict(self):
        self.is_greedy = False
        for tree in self.values():
            if not tree:
                continue  # Exclude leafs
            tree.to_strict()

    def __repr__(self):
        include = f'to_include={self.to_include}'
        exclude = f'to_exclude={self.to_exclude}'
        greedy = f'is_greedy={self.is_greedy}'
        keys = '\n'.join(f'{k}: {v}'.replace('\n', '\n  ') for k, v in self.items())
        keys = f'\n{keys}' if keys else ''
        return f'Tree({include}, {exclude}, {greedy})[{keys}]'


class Rule:
    DELIM = '.'  # Delimiter to separate nested rules
    NEGATION = '-'  # Prefix for negative rules

    def __init__(self, rule: str):
        self.is_negative = rule.startswith(self.NEGATION)
        rule = rule.replace(self.NEGATION, '')
        self.keys = rule.split(self.DELIM)

    def __repr__(self):
        prefix = self.NEGATION if self.is_negative else ""
        return f'{prefix}{self.DELIM.join(self.keys)}'


class Schema:
    def __init__(self, tree: Tree = None):
        self._tree = tree or Tree()

    @property
    def keys(self) -> set:
        return {k for k, t in self._tree.items() if t.to_include}

    @property
    def is_greedy(self) -> bool:
        return self._tree.is_greedy

    def update(self, extend=(), only=()):
        if extend:
            self.apply(rules=extend, is_greedy=True)
        if only:
            self.apply(rules=only, is_greedy=False)

    def apply(self, rules, is_greedy):
        rules_tree = Tree()
        for raw in rules:
            logger.debug('Checking rule:%s', raw)
            rule = Rule(raw)

            current = self._tree
            chain = Tree()
            chain.is_greedy = is_greedy

            keys_num = len(rule.keys)
            new = chain
            for i, k in enumerate(rule.keys):
                is_last_key = keys_num == i + 1
                parent = current
                node = current.get(k, Tree())  # Does not create a new node
                new = new[k]  # Creates a new node

                if not (is_last_key or rule.is_negative) and node.is_greedy:
                    new.is_greedy = is_greedy

                if not node and node.to_exclude:
                    logger.debug('Ignore rule:%s leaf excludes key:%s', raw, k)
                    break

                if rule.is_negative:
                    new.to_exclude = True
                else:
                    new.to_include = True

                if is_last_key:
                    if not parent.is_greedy:
                        logger.debug('Ignore rule:%s parent does not accept new rules', raw)
                    elif rule.is_negative and node.to_include:
                        logger.debug('Ignore rule:%s leaf includes key:%s', raw, k)
                    else:
                        merge_trees(rules_tree, chain)
                else:
                    current = node  # Go deeper

        if rules_tree:
            logger.debug('Updating tree with rules:%s is_greedy:%s', rules, is_greedy)
            merge_trees(self._tree, rules_tree)

    def is_included(self, key: str) -> bool:
        node = self._tree.get(key)
        if self._tree.is_greedy:
            if not node:
                return node is None or not node.to_exclude
            return True
        else:
            return bool(node is not None and node.to_include)

    def fork(self, key: str) -> 'Schema':
        return Schema(tree=self._tree[key])


def merge_trees(old: Tree, *trees):
    for tree in trees:
        # logger.debug('Merging trees:\nold->\n%s\nnew->\n:%s', old, tree)
        old.apply(tree)
        for k in tree.keys():
            merge_trees(old[k], tree[k])
