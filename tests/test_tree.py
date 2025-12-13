import pytest

from sqlalchemy_serializer.lib.schema import Tree, merge_trees


def test_tree_defaults():
    tree = Tree()
    assert tree.to_include is None
    assert tree.to_exclude is None
    assert tree.is_greedy is True
    assert tree.default_factory == Tree
    assert not tree

    assert tree.get("random_key1") is None
    assert isinstance(tree["random_key2"], Tree)
    assert tree


@pytest.mark.parametrize(
    "to_include, to_exclude, is_greedy, props",
    [
        (True, True, False, {}),
        (False, True, True, {"some": "arg", "another": ("one",)}),
    ],
)
def test_tree_init(to_include, to_exclude, is_greedy, props):
    tree = Tree(to_include=to_include, to_exclude=to_exclude, is_greedy=is_greedy, **props)
    assert tree.to_exclude == to_exclude
    assert tree.to_include == to_include
    assert tree.is_greedy == is_greedy
    for k, v in props.items():
        assert tree[k] == v


@pytest.mark.parametrize(
    "tree",
    [
        Tree(key=Tree(first=Tree(another=Tree()), second=Tree())),
        Tree(key=Tree()),
        Tree(),
    ],
)
def test_to_strict_method(tree):
    def check_greed(t):
        assert not t.is_greedy
        for subtree in t.values():
            if subtree:
                check_greed(subtree)
            else:
                assert subtree.is_greedy

    tree.to_strict()
    check_greed(tree)


@pytest.mark.parametrize(
    "is_dummy, is_greedy, to_include, to_exclude",
    [
        (True, True, True, True),
        (True, True, True, False),
        (True, True, False, False),
        (True, False, False, False),
        (False, False, False, False),
        (False, True, False, False),
        (False, True, True, False),
        (False, True, True, True),
    ],
)
def test_tree_apply(is_dummy, is_greedy, to_include, to_exclude):
    tree = Tree() if is_dummy else Tree(some=Tree())
    node = Tree(is_greedy=is_greedy, to_exclude=to_exclude, to_include=to_include)
    tree.apply(node)

    assert tree.is_greedy == is_greedy
    assert tree.to_include == to_include
    assert tree.to_exclude == to_exclude


def test_merge_trees():
    tree1 = Tree(is_greedy=False, to_include=True)
    node1 = tree1["key1"]
    node1.is_greedy = False
    node1.to_include = True

    tree2 = Tree(is_greedy=False, to_exclude=True)
    node2 = tree2["key1"]
    node2.to_exclude = True
    node2.is_greedy = False

    node3 = node2["key2"]
    node3.to_exclude = True
    node3.is_greedy = False

    tree3 = Tree(is_greedy=True, to_include=True)
    node4 = tree3["key1"]
    node4.to_include = True

    node5 = node4["key3"]
    node5.to_include = True

    merge_trees(tree1, tree2, tree3)

    # Check root
    assert not tree1.is_greedy
    assert tree1.to_include
    assert tree1.to_exclude

    # Check the first level
    node = tree1.get("key1")
    assert node
    assert not node.is_greedy
    assert node.to_include
    assert node.to_exclude

    # Check leaves
    leaf = node.get("key2")
    assert leaf is not None
    assert not leaf.is_greedy
    assert leaf.to_exclude
    assert leaf.to_include is None

    leaf = node.get("key3")
    assert leaf is not None
    assert leaf.is_greedy
    assert leaf.to_include
    assert leaf.to_exclude is None
