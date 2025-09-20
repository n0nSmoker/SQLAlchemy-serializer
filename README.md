# SQLAlchemy-serializer
Mixin for SQLAlchemy models serialization without pain.

If you want to serialize SQLAlchemy model instances with only one line of code,
and tools like `marshmallow` seems to be redundant and too complex for such a simple task,
this mixin definitely suits you.

**Contents**
- [Installation](#Installation)
- [Usage](#Usage)
- [Advanced usage](#Advanced-usage)
- [Custom formats](#Custom-formats)
- [Custom types](#Custom-types)
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
item = SomeModel.query.filter(...).one()
result = item.to_dict()
```
You get values of all SQLAlchemy fields in the `result` var, even nested relationships
In order to change the default output you shuld pass tuple of fieldnames as an argument

- If you want to exclude or add some extra fields (not from database)
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
You can use negative rules in `only` param too.
So `item.to_dict(only=('somefield', -'somefield.id'))`
will return `somefiled` without `id`. See [Negative rules in ONLY section](#Negative-rules-in-ONLY-section)

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
# Recursive models and trees
If your models have references to each other or you work with large trees
you need to specify where the serialization should stop.
```python
item.to_dict('-children.children')
```
In this case only the first level of `children` will be included
See [Max recursion](#Max-recursion)

# Custom formats
If you want to change datetime/date/time/decimal format in one model you can specify it like below:
```python
from sqlalchemy_serializer import SerializerMixin

class SomeModel(db.Model, SerializerMixin):
    __tablename__ = 'custom_table_name'

    date_format = '%s'  # Unixtimestamp (seconds)
    datetime_format = '%Y %b %d %H:%M:%S.%f'
    time_format = '%H:%M.%f'
    decimal_format = '{:0>10.3}'

    id = sa.Column(sa.Integer, primary_key=True)
    date = sa.Column(sa.Date)
    datetime = sa.Column(sa.DateTime)
    time = sa.Column(sa.Time)
    money = Decimal('12.123')  # same result with sa.Float(asdecimal=True, ...)
```

If you want to change format in every model, you should write
your own mixin class inherited from `SerializerMixin`:
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

    id = sa.Column(sa.Integer, primary_key=True)
    date = sa.Column(sa.Date)
    datetime = sa.Column(sa.DateTime)
    time = sa.Column(sa.Time)
    money = Decimal('12.123')  # same result with sa.Float(asdecimal=True, ...)

```
All `date/time/datetime/decimal` fields will be serialized using your custom formats.

- Decimal uses python `format` syntax
- To get **unixtimestamp** use `%s`,
- Other `datetime` formats you can find [in docs](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior)


# Custom types
By default the library can serialize the following types:
 ```
 - int
 - str
 - float
 - bytes
 - bool
 - type(None)
 - uuid.UUID
 - time
 - datetime
 - date
 - Decimal
 - Enum
 - dict (if values and keys are one of types mentioned above, or inherit one of them)
 - any Iterable (if types of values are mentioned above, or inherit one of them)
 ```
 If you want to add serialization of any other type or redefine the default behaviour.
 You should add something like this:

```python

serialize_types = (
    (SomeType, lambda x: some_expression),
    (AnyOtherType, some_function)
)
```
To your own mixin class inherited from `SerializerMixin`:

```python
from sqlalchemy_serializer import SerializerMixin
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape

def serialize_int(value):
    return value + 100

class CustomSerializerMixin(SerializerMixin):
    serialize_types = (
        (WKBElement, lambda x: to_shape(x).to_wkt()),
        (int, serialize_int)
    )
```
... or directly to the model:
```python
from geoalchemy2 import Geometry
from sqlalchemy_serializer import SerializerMixin

class Point(Base, SerializerMixin):
    serialize_types = (
        (WKBElement, lambda x: to_shape(x).to_wkt()),
        (AnyOtherType, serialize_smth)
    )
    __tablename__ = 'point'
    id = Column(Integer, primary_key=True)
    position = Column(Geometry('POINT'))
```

Unfortunately you can not access formats or tzinfo in that functions.
I'll implement this logic later if any of users needs it.


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
# Helpers
## serialize_collection
If you want to do the following in one line
```python
categories = Category.query.all()
response = [category.to_dict(**some_params) for category in categories]
```
use helper
```python
from sqlalchemy_serializer import serialize_collection

response = serialize_collection(Category.query.all(), **some_params)

```
# Troubleshooting

## Max recursion
If you've faced with **maximum recursion depth exceeded** exception,
most likely the serializer have found instance of the same class somewhere among model's relationships.
Especially if you use backrefs. In this case you need to tell it where to stop like below:
```python
class User(Base, SerializerMixin):
    __tablename__ = 'users'

    # Exclude nested model of the same class to avoid max recursion error
    serialize_rules = ('-related_models.user',)
    ...
    related_models = relationship("RelatedModel", backref='user')


class RelatedModel(Base, SerializerMixin):
    __tablename__ = 'some_table'

    ...
    user_id = Column(Integer, ForeignKey('users.id'))
    ...
```
If for some reason you need the field `user` to be presented in `related_models` field.
You can change `serialize_rules` to `('-related_models.user.related_models',)`
To break the chain of serialisation a bit further.
[Recursive models and trees](#Recursive-models-and-trees)

## Controversial rules
If you add controversial rules like `serialize_rules = ('-prop', 'prop.id')`
The serializer will include `prop` in spite of `-prop` rule.

## Negative rules in ONLY section
If you pass rules in `serialize_only` the serializer becomes **NOT** greedy and returns **ONLY** fields listed there.
So `serialize_only = ('-model.id',)` will return nothing
But `serialize_only = ('model', '-model.id',)` will return `model` field without `id`

## One element tuples
Do not forget to add **comma** at the end of one element tuples, it is trivial,
but a lot of developers forget about it:
```python
serialize_only = ('some_field',)  # <--- Thats right!
serialize_only = ('some_field')  # <--- WRONG it is actually not a tuple

```

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
