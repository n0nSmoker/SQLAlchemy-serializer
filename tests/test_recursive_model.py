from .models import RecursiveModel


def test_no_rules(get_instance):
    """Checks to_dict method of model without rules"""
    root = get_instance(RecursiveModel)
    child_full = get_instance(RecursiveModel, parent_id=root.id)
    _ = get_instance(RecursiveModel, parent_id=child_full.id)

    # No rules
    data = root.to_dict()

    assert "children" in data
    assert "children" in data["children"][0]
    assert "children" in data["children"][0]["children"][0]

    assert "name" in data
    assert "name" in data["children"][0]
    assert "name" in data["children"][0]["children"][0]


def test_rules_in_class(get_instance):
    """Checks to_dict method of model with rules
    defined on class level
    """
    root = get_instance(RecursiveModel)
    child_full = get_instance(RecursiveModel, parent_id=root.id)
    _ = get_instance(RecursiveModel, parent_id=child_full.id)

    RecursiveModel.serialize_rules = ("-children.children.children",)
    data = root.to_dict()

    assert "children" in data
    assert "children" in data["children"][0]
    assert "children" not in data["children"][0]["children"][0]

    assert "name" in data
    assert "name" in data["children"][0]
    assert "name" in data["children"][0]["children"][0]


def test_rules_in_method_call(get_instance):
    """Checks to_dict method of model with rules
    passed in to_dict method
    """
    root = get_instance(RecursiveModel)
    child_full = get_instance(RecursiveModel, parent_id=root.id)
    _ = get_instance(RecursiveModel, parent_id=child_full.id)

    RecursiveModel.serialize_rules = ()
    data = root.to_dict(rules=("-children.children.children",))

    assert "children" in data
    assert "children" in data["children"][0]
    assert "children" not in data["children"][0]["children"][0]

    assert "name" in data
    assert "name" in data["children"][0]
    assert "name" in data["children"][0]["children"][0]


def test_combination_of_rules(get_instance):
    """Checks to_dict method of model with combinations of
    rules passed in to_dict method
    """
    root = get_instance(RecursiveModel)
    child_full = get_instance(RecursiveModel, parent_id=root.id)
    _ = get_instance(RecursiveModel, parent_id=child_full.id)

    RecursiveModel.serialize_rules = ("-children.children", "-children.id")
    data = root.to_dict()

    assert "children" in data
    assert "children" not in data["children"][0]

    assert "name" in data
    assert "name" in data["children"][0]

    assert "id" in data
    assert "id" not in data["children"][0]
