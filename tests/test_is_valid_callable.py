"""Tests for Serializer.is_valid_callable static method."""

import inspect
from types import MethodType

import sqlalchemy as sa

from sqlalchemy_serializer import SerializerMixin
from sqlalchemy_serializer.serializer import Serializer

from .models import Base


def test_is_valid_callable_with_varargs():
    """Test that functions with *args are not valid callables."""

    def func_with_args(*args):
        return args

    assert Serializer.is_valid_callable(func_with_args) is False


def test_is_valid_callable_with_varkw():
    """Test that functions with **kwargs are not valid callables."""

    def func_with_kwargs(**kwargs):
        return kwargs

    assert Serializer.is_valid_callable(func_with_kwargs) is False


def test_is_valid_callable_with_both_varargs_and_varkw():
    """Test that functions with both *args and **kwargs are not valid callables."""

    def func_with_both(*args, **kwargs):
        return args, kwargs

    assert Serializer.is_valid_callable(func_with_both) is False


def test_is_valid_callable_method_without_self():
    """Test that MethodType without 'self' as first arg is not valid callable."""

    class ModelWithClassMethod(Base, SerializerMixin):
        __tablename__ = "model_with_classmethod"
        serialize_only = ()
        serialize_rules = ()

        id = sa.Column(sa.Integer, primary_key=True)
        string = sa.Column(sa.String(256), default="test")

        @classmethod
        def class_method(cls) -> str:
            return "result"

    model = ModelWithClassMethod(id=1, string="test")
    method = model.class_method

    # Verify it's a MethodType
    assert isinstance(method, MethodType)

    # Should return False because first arg is 'cls', not 'self'
    assert Serializer.is_valid_callable(method) is False


def test_is_valid_callable_method_with_empty_args():
    """Test that MethodType with no args (not even self) is not valid callable."""

    # Create a function with no args
    def func_no_args():
        return "result"

    # Manually create a MethodType bound to an object
    # This simulates a method with no args
    # (which shouldn't happen in normal Python, but tests the edge case)
    class DummyObj:
        pass

    obj = DummyObj()
    # Bind the function as a method
    method = MethodType(func_no_args, obj)

    # Verify it's a MethodType
    assert isinstance(method, MethodType)

    # Verify it has no args
    # inspect.getfullargspec on bound method returns underlying function's args
    spec = inspect.getfullargspec(method)
    assert not spec.args

    # Should return False because no args
    assert Serializer.is_valid_callable(method) is False
