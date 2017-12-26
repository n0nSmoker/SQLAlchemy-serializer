# SQLAlchemy-serializer
Mixin for sqlalchemy-models serialization without pain.

If you want SQLAlchemy model to become serializable,
add **SerializerMixin** in class definition:
```python
class SomeModel(db.Model, SerializerMixin):
    ...
```

This mixin adds **.to_dict()** method to model instances.
So now if you can do something like this:
```python
item = SomeModel.query.filter(.....).one()
result = item.to_dict()
```
You'll get values of all SQLAlchemy fields in result, even nested relationship

If you want to exclude a few fields for this exact item:
```python
result = item.to_dict(extend=('-somefield', '-anotherone.nestedfield.even_a_list'))
```

If you want to add a field which is not defined as an SQLAlchemy field:
```python
class SomeModel(db.Model, SerializerMixin):
    non_sql_field = 123

    def a_method(self):
        return anything

result = item.to_dict(extend=('non_sql_field', 'a_method'))
```
Note that method or a function should have no arguments except ***self***,
in order to let serializer call it without hesitations.

If you want to get exact fields:
```python

result = item.to_dict(only=('non_sql_field', 'a_method', 'somefield'))
```
Note that if ***somefield*** is an SQLAlchemy instance, you get all it's
serializable fields.

If you want to define schema for all instances of particular SQLAlchemy model:

```python
class SomeModel(db.Model, SerializerMixin):
    __schema_only__ = ('somefield', '-somefield.id')
    __schema_extend__ = ()
    somefield = db.relationship('AnotherModel')

result = item.to_dict()
```
***__schema_only__*** and  ***__schema_extend__*** work the same way as ***to_dict's*** arguments



# Detailed example (For more examples see tests):

```python
class FlatModel(db.Model, SerializerMixin):
    __schema_only__ = ('non_sqlalchemy_field', '-id')
    __schema_extend__ = ()

    __tablename__ = 'test_flat_model'
    id = db.Column(db.Integer, primary_key=True)
    string = db.Column(db.String(256), default='Some string!')
    time_at = db.Column(db.DateTime, default=datetime.utcnow())
    date_at = db.Column(db.Date, default=datetime.utcnow())
    boolean = db.Column(db.Boolean, default=True)
    boolean2 = db.Column(db.Boolean, default=False)
    null = db.Column(db.String)
    non_sqlalchemy_dict = dict(qwerty=123)


class ComplexModel(db.Model, SerializerMixin):
    # schema is not defined so
    # we will get all SQLALCHEMY attributes of the instance by default

    __tablename__ = 'test_complex_model'
    id = db.Column(db.Integer, primary_key=True)
    string = db.Column(db.String(256), default='Some string!')
    boolean = db.Column(db.Boolean, default=True)
    null = db.Column(db.String)
    flat_id = db.Column(db.ForeignKey('test_flat_model.id', ondelete='CASCADE'))
    rel = db.relationship('FlatModel', lazy='joined', uselist=False)
    non_sqlalchemy_list = [dict(a=12, b=10), dict(a=123, b=12)]

instance = ComplexModel.query.first()


# Lazy mode =)

instance.to_dict()

dict(
    id=1,
    string='Some string!',
    boolean=True,
    null=None,
    flat_id=1,
    rel=dict(
        # id is skipped because in defined in __schema__ with '-' simbol
        string='Some string!',
        time_at=datetime...,
        date_at=date...,
        boolean=True,
        boolean2=False,
        null=None,
        non_sqlalchemy_dict=dict(qwerty=123)
)


# Extend schema

instance.to_dict(extend=('-id', 'rel.id', 'non_sqlalchemy_list'))

dict(
    string='Some string!',
    boolean=True,
    null=None,
    flat_id=1,
    non_sqlalchemy_list=[dict(a=12, b=10), dict(a=123, b=12)],
    rel=dict(
        id=1,
        string='Some string!',
        time_at=datetime...,
        date_at=date...,
        boolean=True,
        boolean2=False,
        null=None,
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

