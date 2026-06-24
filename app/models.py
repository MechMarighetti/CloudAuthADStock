from app import db
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
    
    def roles_list(self):
        return [r for r in (self.roles or '').split(',') if r]

    def has_role(self, role: str) -> bool:
        return role in self.roles_list()


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    genero = db.Column(db.String(50), nullable=False)
    altura = db.Column(db.String(20))  # 'baja', 'media', 'alta'
    tipo_servicio = db.Column(db.String(10))  # 'SaaS', 'PaaS', 'IaaS'
    capacidad_almacenamiento = db.Column(db.Float)  # GB
    capacidad_procesamiento = db.Column(db.Float)   # vCPUs
    memoria_ram = db.Column(db.Float)              # GB
    precio_mensual = db.Column(db.Float)
    escalable = db.Column(db.Boolean, default=True)
    descripcion = db.Column(db.Text)
    stock_disponible = db.Column(db.Integer, default=0)


class Movement(db.Model):
    __tablename__ = 'movements'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    tipo = db.Column(db.String(20))  # 'entrada' or 'salida'
    cantidad = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.Column(db.String(150))

    producto = db.relationship('Product', backref=db.backref('movements', lazy=True))

