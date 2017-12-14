# SQLAlchemy-serializer
Mixin for sqlalchemy-models serialization without pain.


# Usage (more examples in tests):

```python


class FlatModel(db.Model, SerializerMixin):

    # Define default schema here if you need
    # or NON sqlalchemy attributes otherwise they will not be included
    # You can use dot notation to define nested attributes
    __schema__ = ('non_sqlalchemy_field', '-id')

    __tablename__ = 'test_flat_model'
    id = db.Column(db.Integer, primary_key=True)
    string = db.Column(db.String(256), default='Some string with КИРИЛИК СИМБОЛЗ!')
    time_at = db.Column(db.DateTime, default=datetime.utcnow())
    date_at = db.Column(db.Date, default=datetime.utcnow())
    boolean = db.Column(db.Boolean, default=True)
    boolean2 = db.Column(db.Boolean, default=False)
    null = db.Column(db.String)
    non_sqlalchemy_field = dict(qwerty=123)


class ComplexModel(db.Model, SerializerMixin):

    # schema is not defined so
    # we will get all SQLALCHEMY attributes of the instance by default

    __tablename__ = 'test_nested_model'
    id = db.Column(db.Integer, primary_key=True)
    string = db.Column(db.String(256), default='Some string with КИРИЛИК СИМБОЛЗ!')
    boolean = db.Column(db.Boolean, default=True)
    null = db.Column(db.String)
    flat_id = db.Column(db.ForeignKey('test_flat_model.id', ondelete='CASCADE'))
    rel = db.relationship('FlatModel', lazy='joined', uselist=False)


instance = ComplexModel.query.first()


# Lazy mode =)

instance.to_dict()

dict(
    id=1,
    string='Some string with КИРИЛИК СИМБОЛЗ!',
    boolean=True,
    null=None,
    flat_id=1,
    rel=dict(
        # id is skipped because in defined in __schema__ with '-' simbol
        string='Some string with КИРИЛИК СИМБОЛЗ!',
        time_at=datetime...,
        date_at=date...,
        boolean=True,
        boolean2=False,
        null=None,
        non_sqlalchemy_field=dict(qwerty=123)
)


# Extend schema

instance.to_dict(extend=('-id', 'rel.id'))

dict(
    string='Some string with КИРИЛИК СИМБОЛЗ!',
    boolean=True,
    null=None,
    flat_id=1,
    rel=dict(
        id=1,
        string='Some string with КИРИЛИК СИМБОЛЗ!',
        time_at=datetime...,
        date_at=date...,
        boolean=True,
        boolean2=False,
        null=None,
        non_sqlalchemy_field=dict(qwerty=123)
)


# Replace schema

instance.to_dict(schema=('id', 'flat_id', 'rel.id'))

dict(
    id=1,
    flat_id=1,
    rel=dict(
        id=1
)

```
