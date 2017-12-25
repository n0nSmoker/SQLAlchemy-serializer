from datetime import datetime
from flask_builder import db
from sqlalchemy_serializer import SerializerMixin


class NoRelationshipModel(db.Model, SerializerMixin):
    __tablename__ = 'no_rel_model'
    id = db.Column(db.Integer, primary_key=True)
    string = db.Column(db.String(256), default='Some string with')
    time_at = db.Column(db.DateTime, default=datetime.utcnow())
    date_at = db.Column(db.Date, default=datetime.utcnow())
    boolean = db.Column(db.Boolean, default=True)
    null = db.Column(db.String)
    nosql_field = None

    def _method(self):
        return 'User defined method %s' % self.string


class Many2OneModel(db.Model, SerializerMixin):
    __tablename__ = 'many2one_model'
    id = db.Column(db.Integer, primary_key=True)
    string = db.Column(db.String(256), default='Some string')
    boolean = db.Column(db.Boolean, default=True)
    null = db.Column(db.String)
    rel_id = db.Column(db.ForeignKey('many2many_model.id', ondelete='CASCADE'))
    rel = db.relationship('Many2manyModel', lazy='joined', uselist=False)


secondary = db.Table(
    'secondary_table',
    db.Column('no_rel_id', db.Integer, db.ForeignKey('no_rel_model.id', ondelete='CASCADE'), primary_key=True),
    db.Column('m2m_id', db.Integer, db.ForeignKey('many2many_model.id', ondelete='CASCADE'), primary_key=True)
)


class Many2manyModel(db.Model, SerializerMixin):
    __tablename__ = 'many2many_model'
    id = db.Column(db.Integer, primary_key=True)
    string = db.Column(db.String(256), default='Some string for m2m')
    boolean = db.Column(db.Boolean, default=True)
    null = db.Column(db.String)
    rel = db.relationship(NoRelationshipModel, lazy='joined', secondary=secondary)

