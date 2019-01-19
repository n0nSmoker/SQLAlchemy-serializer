# SQLAlchemy-serializer
Mixin for sqlalchemy-models serialization without pain.

## Installation

```
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
You'll get values of all SQLAlchemy fields in the `result` var, even nested relationships

If you want to exclude a few fields for this exact item:
```python
result = item.to_dict(rules=('-somefield', '-anotherone.nested1.nested2'))
```

If you want to add a field which is not defined as an SQLAlchemy field:
```python
class SomeModel(db.Model, SerializerMixin):
    non_sql_field = 123

    def a_method(self):
        return anything

result = item.to_dict(rules=('non_sql_field', 'a_method'))
```
Note that method or a function should have no arguments except ***self***,
in order to let serializer call it without hesitations.

If you want to get exact fields:
```python

result = item.to_dict(only=('non_sql_field', 'a_method', 'somefield'))
```
Note that if ***somefield*** is an SQLAlchemy instance, you get all it's
serializable fields.

If you want to define schema for all instances of particular SQLAlchemy model,
add serialize properties to model definition:

```python
class SomeModel(db.Model, SerializerMixin):
    serialize_only = ('somefield.id',)
    serialize_rules = ()
    ...
    somefield = db.relationship('AnotherModel')

result = item.to_dict()
{'somefield':[{'id':...}]}

```
***serialize_only*** and  ***serialize_rules*** work the same way as ***to_dict's*** arguments


# Detailed example (For more examples see tests):

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
   """

    id = db.Column(db.Integer, primary_key=True)
    string = db.Column(db.String(256), default='Some string!')
    boolean = db.Column(db.Boolean, default=True)
    null = db.Column(db.String)
    flat_id = db.Column(db.ForeignKey('test_flat_model.id'))
    rel = db.relationship('FlatModel')
    non_sqlalchemy_list = [dict(a=12, b=10), dict(a=123, b=12)]

instance = ComplexModel.query.first()


# Now by default the result looks like this:

instance.to_dict()
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

instance.to_dict(rules=('-id', '-rel.id', 'rel.string', 'non_sqlalchemy_list'))

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


# Exclusive schema

instance.to_dict(only=('id', 'flat_id', 'rel.id', 'non_sqlalchemy_list.a'))

dict(
    id=1,
    flat_id=1,
    non_sqlalchemy_list=[dict(a=12), dict(a=123)],
    rel=dict(
        id=1
    )

```

# Troubleshooting
If you've faced with 'maximum recursion depth exceeded' exception,
most likely serializer have found instance of the same class somewhere among model's relationships.
You need to exclude it from schema or specify the exact properties to serialize.


