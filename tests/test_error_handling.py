"""Error handling tests for SQLAlchemy serializer."""

import pytest
import sqlalchemy as sa

from sqlalchemy_serializer import SerializerMixin

from .models import Base


class ModelWithFailingProperty(Base, SerializerMixin):
    """Model with a property that raises an exception."""

    __tablename__ = "model_with_failing_property"
    serialize_only = ()
    serialize_rules = ()

    id = sa.Column(sa.Integer, primary_key=True)
    string = sa.Column(sa.String(256), default="test")

    @property
    def failing_prop(self):
        """Property that raises an exception."""
        raise ValueError("Property access failed")

    @property
    def valid_prop(self):
        """Property that works correctly."""
        return "valid value"


class ModelWithFailingMethod(Base, SerializerMixin):
    """Model with a method that raises an exception."""

    __tablename__ = "model_with_failing_method"
    serialize_only = ()
    serialize_rules = ()

    id = sa.Column(sa.Integer, primary_key=True)
    string = sa.Column(sa.String(256), default="test")

    def failing_method(self):
        """Method that raises an exception."""
        raise RuntimeError("Method call failed")

    def valid_method(self):
        """Method that works correctly."""
        return "valid result"


class ModelWithFailingCustomSerializer(Base, SerializerMixin):
    """Model with custom serializer that raises an exception."""

    __tablename__ = "model_with_failing_custom_serializer"
    serialize_only = ()
    serialize_rules = ()

    id = sa.Column(sa.Integer, primary_key=True)
    string = sa.Column(sa.String(256), default="test")
    number = sa.Column(sa.Integer, default=42)


def test_property_raises_exception_default_behavior(get_instance):
    model = get_instance(ModelWithFailingProperty)

    with pytest.raises(ValueError, match="Property access failed"):
        model.to_dict(rules=("failing_prop",))


def test_method_raises_exception_default_behavior(get_instance):
    model = get_instance(ModelWithFailingMethod)

    with pytest.raises(RuntimeError, match="Method call failed"):
        model.to_dict(rules=("failing_method",))


def test_custom_serializer_raises_exception_default_behavior(get_instance):
    model = get_instance(ModelWithFailingCustomSerializer)

    def failing_serializer(_value):
        """Custom serializer that raises an exception."""
        raise TypeError("Custom serializer failed")

    with pytest.raises(TypeError, match="Custom serializer failed"):
        model.to_dict(serialize_columns={"string": failing_serializer})
