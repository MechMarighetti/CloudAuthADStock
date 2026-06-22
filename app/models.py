from . import db
from flask_login import UserMixin
from datetime import datetime


class ADUser(db.Model, UserMixin):
    __tablename__ = 'ad_users'
    username = db.Column(db.String(150), primary_key=True)
    display_name = db.Column(db.String(200))
    roles = db.Column(db.String(200))  # comma-separated AD groups
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

    def get_id(self):
        return self.username


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    stock_actual = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=0)
    precio = db.Column(db.Float, default=0.0)


class Movement(db.Model):
    __tablename__ = 'movements'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    tipo = db.Column(db.String(20))  # 'entrada' or 'salida'
    cantidad = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.Column(db.String(150))

    producto = db.relationship('Product', backref=db.backref('movements', lazy=True))
