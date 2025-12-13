import pytest

from sqlalchemy_serializer.lib.schema import Rule, Schema, Tree


@pytest.mark.parametrize("tree", [None, Tree(to_include=False)])
def test_init_method(tree):
    schema = Schema(tree=tree)
    assert isinstance(schema._tree, Tree)
    if not tree:
        assert schema._tree.to_include is None
    else:
        assert not schema._tree.to_include


@pytest.mark.parametrize(
    "rules, keys",
    [
        ({"extend": ("key.another",)}, {"key"}),
        ({"extend": ("key.another", "-key")}, {"key"}),
        ({"extend": ("key.another", "-key.another")}, {"key"}),
        ({"only": ("key.another", "-key.another")}, {"key"}),
        ({"only": ("-key.another",)}, set()),
        ({"only": ("key.another",), "extend": ("another",)}, {"key", "another"}),
    ],
)
def test_keys_property(rules, keys):
    schema = Schema()
    schema.update(**rules)
    assert schema.keys == keys


@pytest.mark.parametrize(
    "rules, expected",
    [
        ({"extend": ("key.another",)}, True),
        ({"extend": ("key.another", "-key")}, True),
        ({"extend": ("key.another", "-key.another")}, True),
        ({"only": ("key.another", "-key.another")}, False),
        ({"only": ("-key.another",)}, False),
        ({"only": ("key.another",), "extend": ("another",)}, False),
    ],
)
def test_is_greedy_property(rules, expected):
    schema = Schema()
    schema.update(**rules)
    assert schema.is_greedy is expected


@pytest.mark.parametrize(
    "old, new, expected",
    [
        (
            {"extend": ("new.o.o", "old.o.o")},
            {"only": ("old",)},
            {
                "": False,  # root
                "new": False,
                "new.o": False,
                "new.o.o": True,
                "old": True,
                "old.o": True,
                "old.o.o": True,
            },
        ),
    ],
)
def test_is_greedy_updated(old, new, expected):
    schema = Schema()
    schema.update(**old)
    schema.update(**new)
    assert schema.is_greedy == expected.pop("")
    for rule, is_greedy in expected.items():
        leaf = check_rule(rule, schema._tree)
        assert leaf.is_greedy == is_greedy


@pytest.mark.parametrize(
    "old, new, expect",
    [
        (
            # Controversial rules
            {"extend": ("-o", "o.o")},
            {},
            ("-o", "o.o"),
        ),
        ({"extend": ("-o",)}, {"extend": ("-o.o",)}, ("-o",)),
        ({"extend": ("-o",)}, {"extend": ("o",)}, ("-o",)),
        ({"extend": ("o",)}, {"extend": ("-o",)}, ("o",)),
        ({"extend": ("o.o",)}, {"extend": ("-o.one",)}, ("o.o", "-o.one")),
        (
            {"extend": ("-o.o.o",)},
            {"extend": ("o.o.another",)},
            ("-o.o.o", "o.o.another"),
        ),
        (
            {"only": ("o.o",)},
            {"extend": ("o.another", "-o.o.o")},
            (
                "o.o",
                "-o.o.o",
                "!o.another",
            ),  # Prefix "!" means there should not be that rule
        ),
        (
            {"extend": ("o.o",)},
            {"only": ("o.another", "-o.o.o")},
            ("o.o", "-o.o.o", "o.another"),
        ),
        (
            {"extend": ("o.o",)},
            {"only": ("o.another", "-o.o.o")},
            ("o.o", "-o.o.o", "o.another"),
        ),
        (
            {"extend": ("o.o.o", "o.another.o", "o.o.another")},
            {"only": ("o.another", "-o.o.another")},
            ("o.o.o", "o.another.o", "o.o.another"),
        ),
    ],
)
def test_update_method(old, new, expect):
    """Checks if the schema merges rules correctly"""
    schema = Schema()
    schema.update(**old)
    schema.update(**new)

    assert schema._tree.is_greedy == bool(not (old.get("only") or new.get("only")))
    for rule in expect:
        if rule.startswith("!"):
            with pytest.raises(NoNodeException):
                check_rule(text=rule[1:], tree=schema._tree)
        else:
            check_rule(text=rule, tree=schema._tree)


@pytest.mark.parametrize(
    "args, expected",
    [
        (
            # Conflicted rules, negative rule have higher priority
            {"extend": ("key", "-key")},
            False,
        ),
        ({"extend": ("-key",)}, False),
        ({"extend": ("another",)}, True),
        ({"extend": ("-another",)}, True),
        ({"extend": ("-key.another",)}, True),
        ({"extend": ("key.another",)}, True),
        (
            {
                "extend": (
                    "key",
                    "-key.another",
                )
            },
            True,
        ),
        (
            # Conflicted rules, positive rule have higher priority
            {"only": ("key", "-key")},
            True,
        ),
        ({"only": ("-key",)}, False),
        ({"only": ("another",)}, False),
        ({"only": ("key", "-another")}, True),
        ({"only": ("key",)}, True),
        ({"only": ("key.another",)}, True),
        ({"only": ("-key.another",)}, False),
        (
            {
                "only": (
                    "key",
                    "-key.another",
                )
            },
            True,
        ),
    ],
)
def test_is_included_method(args, expected):
    KEY = "key"
    schema = Schema()
    schema.update(**args)
    assert schema.is_included(KEY) == expected


@pytest.mark.parametrize(
    "args, new_args, is_greedy",
    [
        (
            {"extend": ("key.key", "-key.key.key")},
            {},
            True,
        ),
        (
            {"extend": ("-key.another",)},
            {"only": ("key",)},
            True,
        ),
        (
            {"only": ("-key.another",)},
            {"extend": ("key",)},
            True,
        ),
        (
            {"extend": ("-key.another",)},
            {"extend": ("key",)},
            True,
        ),
        (
            {"only": ("key",)},
            {"extend": ("-key.another",)},
            True,
        ),
        (
            {"only": ("key.another",)},
            {"extend": ("-key.another2",)},
            False,
        ),
        (
            {"extend": ("key.another",)},
            {"only": ("key.another2",)},
            False,
        ),
    ],
)
def test_fork_method(args, new_args, is_greedy):
    KEY = "key"
    schema = Schema()
    schema.update(**args)
    schema.update(**new_args)
    forked = schema.fork(KEY)
    assert forked.is_greedy is is_greedy


def check_rule(text: str, tree: Tree) -> Tree:
    """Checks that the rule is correctly stored in the tree
    and returns the leaf
    """
    rule = Rule(text)
    for k in rule.keys:
        tree = tree.get(k)
        if tree is None:
            raise NoNodeException(f"Can not find key:{k} in tree:{tree}")
        if rule.is_negative:
            assert tree.to_exclude
        else:
            assert tree.to_include
    return tree


class NoNodeException(Exception):
    pass
