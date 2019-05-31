# SQLAlchemy-serializer
Mixin for SQLAlchemy models serialization without pain.

If you want to serialize SQLAlchemy model instances with only one line of code,
and tools like `marshmallow` seems to be redundant and too complex for such a simple task,
this mixin definitely suits you.

**Contents**
- [Installation](#Installation)
- [Usage](#Usage)
- [Advanced usage](#Advanced-usage)
- [Customization](#Customization)
- [Timezones](#Timezones)
- [Troubleshooting](#Troubleshooting)
- [Tests](#Tests)

## Installation

```bash
pip install SQLAlchemy-serializer
```

## Usage

If you want SQLAlchemy model to become serializable,
add **SerializerMixin** in class definition:
```python
from sqlalchemy_serializer import SerializerMixin


class SomeModel(db.Model, SerializerMixin):
    ...
```

This mixin adds **.to_dict()** method to model instances.
So now you can do something like this:
```python
item = SomeModel.query.filter(.....).one()
result = item.to_dict()
```
You get values of all SQLAlchemy fields in the `result` var, even nested relationships
In order to change the default output you shuld pass tuple of fieldnames as an argument

- If you want to exclude or add some extra fields (not from dataase) 
  You should pass `rules` argument
- If you want to define the only fields to be presented in serializer's output
  use `only` argument

If you want to exclude a few fields for this exact item:
```python
result = item.to_dict(rules=('-somefield', '-some_relation.nested_one.another_nested_one'))
```

If you want to add a field which is not defined as an SQLAlchemy field:
```python
class SomeModel(db.Model, SerializerMixin):
    non_sql_field = 123

    def method(self):
        return anything

result = item.to_dict(rules=('non_sql_field', 'method'))
```
**Note** that method or a function should have no arguments except ***self***,
in order to let serializer call it without hesitations.

If you want to get exact fields:
```python

result = item.to_dict(only=('non_sql_field', 'method', 'somefield'))
```
**Note** that if ***somefield*** is an SQLAlchemy instance, you get all it's
serializable fields. So if you want to get only some of them, you should define it like below:
```python

result = item.to_dict(only=('non_sql_field', 'method', 'somefield.id', 'somefield.etc'))
```

If you want to define schema for all instances of particular SQLAlchemy model,
add serialize properties to model definition:
```python
class SomeModel(db.Model, SerializerMixin):
    serialize_only = ('somefield.id',)
    serialize_rules = ()
    ...
    somefield = db.relationship('AnotherModel')

result = item.to_dict()
```
So the `result` in this case will be `{'somefield': [{'id': some_id}]}`
***serialize_only*** and  ***serialize_rules*** work the same way as ***to_dict's*** arguments


# Advanced usage 
For more examples see [tests](https://github.com/n0nSmoker/SQLAlchemy-serializer/tree/master/tests)

```python
class FlatModel(db.Model, SerializerMixin):
    """
    to_dict() of all instances of this model now returns only following two fields
    """
    serialize_only = ('non_sqlalchemy_field', 'id')
    serialize_rules = ()

    id = db.Column(db.Integer, primary_key=True)
    string = db.Column(db.String(256), default='Some string!')
    time = db.Column(db.DateTime, default=datetime.utcnow())
    date = db.Column(db.Date, default=datetime.utcnow())
    boolean = db.Column(db.Boolean, default=True)
    boolean2 = db.Column(db.Boolean, default=False)
    null = db.Column(db.String)
    non_sqlalchemy_dict = dict(qwerty=123)


class ComplexModel(db.Model, SerializerMixin):
   """
   Schema is not defined so
   we will get all SQLAlchemy attributes of the instance by default
   without `non_sqlalchemy_list`
   """

    id = db.Column(db.Integer, primary_key=True)
    string = db.Column(db.String(256), default='Some string!')
    boolean = db.Column(db.Boolean, default=True)
    null = db.Column(db.String)
    flat_id = db.Column(db.ForeignKey('test_flat_model.id'))
    rel = db.relationship('FlatModel')
    non_sqlalchemy_list = [dict(a=12, b=10), dict(a=123, b=12)]

item = ComplexModel.query.first()


# Now by default the result looks like this:
item.to_dict()

dict(
    id=1,
    string='Some string!',
    boolean=True,
    null=None,
    flat_id=1,
    rel=[dict(
        id=1,
        non_sqlalchemy_dict=dict(qwerty=123)
    )]


# Extend schema
item.to_dict(rules=('-id', '-rel.id', 'rel.string', 'non_sqlalchemy_list'))

dict(
    string='Some string!',
    boolean=True,
    null=None,
    flat_id=1,
    non_sqlalchemy_list=[dict(a=12, b=10), dict(a=123, b=12)],
    rel=dict(
        string='Some string!',
        non_sqlalchemy_dict=dict(qwerty=123)
    )
)


# Exclusive schema
item.to_dict(only=('id', 'flat_id', 'rel.id', 'non_sqlalchemy_list.a'))

dict(
    id=1,
    flat_id=1,
    non_sqlalchemy_list=[dict(a=12), dict(a=123)],
    rel=dict(
        id=1
    )
)
```

# Customization
If you want to change datetime/date/time/decimal formats for all models you should write
your own mixin class inherited from `SerializerMixin` like in example below:

```python
from sqlalchemy_serializer import SerializerMixin

class CustomSerializerMixin(SerializerMixin):
    date_format = '%s'  # Unixtimestamp (seconds)
    datetime_format = '%Y %b %d %H:%M:%S.%f'
    time_format = '%H:%M.%f'
    decimal_format = '{:0>10.3}'
```
And later use it as usual:
```python
from decimal import Decimal
import sqlalchemy as sa
from some.lib.package import CustomSerializerMixin


class CustomSerializerModel(db.Model, CustomSerializerMixin):
    __tablename__ = 'custom_table_name'
    serialize_only = ()
    serialize_rules = ()

    id = sa.Column(sa.Integer, primary_key=True)
    date = sa.Column(sa.Date)
    datetime = sa.Column(sa.DateTime)
    time = sa.Column(sa.Time)
    money = Decimal('12.123')  # the same result with sa.Float(asdecimal=True, ...)

```
All `date/time/datetime/decimal` fields will be serialized using your custom formats.

- Decimal uses python `format` syntax
- To get **unixtimestamp** use `%s`, 
- Other `datetime` formats you can find [in docs](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior)

# Timezones
To keep `datetimes` consistent its better to store it in the database normalized to **UTC**.
But when you return response, sometimes (mostly in web, mobile applications can do it themselves)
you need to convert all `datetimes` to user's timezone.
So you need to tell serializer what timezone to use.
There are two ways to do it:
-  The simplest one is to pass timezone directly as an argument for `to_dict` function
```python
import pytz

item.to_dict(timezone=pytz.timezone('Europe/Moscow'))
```
- But if you do not want to write this code in every function, you should define
  timezone logic in your custom mixin (how to use customized mixin see [Castomization](#Castomization))
 ```python
import pytz
from sqlalchemy_serializer import SerializerMixin
from some.package import get_current_user

class CustomSerializerMixin(SerializerMixin):
    def get_tzinfo(self):
        # you can write your own logic here, 
        # the example below will work if you store timezone
        # in user's profile
        return pytz.timezone(get_current_user()['timezone'])
```

# Troubleshooting
If you've faced with **maximum recursion depth exceeded** exception,
most likely serializer have found instance of the same class somewhere among model's relationships.
You need to exclude it from schema or specify the exact properties to serialize.


# Tests
To run tests and see tests coverage report just type the following command:(doker and doker-compose should be installed on you local machine)
```bash
make test
```
To run a particular test use
```bash
make test file=tests/some_file.py
make test file=tests/some_file.py::test_func
```

I will appreciate any help in improving this library, so feel free to submit issues or pull requests.

