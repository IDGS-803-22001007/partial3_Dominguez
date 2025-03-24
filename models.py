from flask_sqlalchemy import SQLAlchemy
import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash  # Importa las funciones

db = SQLAlchemy()

class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50))
    direccion = db.Column(db.String(50))
    telefono = db.Column(db.String(50))
    created_date = db.Column(db.DateTime, default=datetime.datetime.now)

class Pedidos(db.Model):
    __tablename__ = 'pizza'
    id = db.Column(db.Integer, primary_key=True)
    tamanio = db.Column(db.String(50))
    ingredientes = db.Column(db.String(50))
    cantidad = db.Column(db.Integer)
    created_date = db.Column(db.DateTime, default=datetime.datetime.now)

class Venta(db.Model):
    __tablename__ = 'ventas'
    idVenta = db.Column(db.Integer, primary_key=True)
    idPedido = db.Column(db.Integer, db.ForeignKey('pizza.id'), nullable=False)
    # Añadir esta línea para relacionar con Cliente
    idCliente = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    fechaVenta = db.Column(db.DateTime, default=datetime.datetime.now)
    montoTotal = db.Column(db.Float, nullable=False)
    size = db.Column(db.String(20), nullable=False)
    ingredientes = db.Column(db.String(200), nullable=False)
    num_pizzas = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    # Relación con Cliente
    cliente = db.relationship('Cliente', backref='ventas')

    # Relación con Pedidos
    pedido = db.relationship('Pedidos', backref='ventas')
    

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f"<Usuario {self.username}>"

    def check_password(self, password):
        # Asegúrate de comparar la contraseña de la forma correcta
        return self.password == password
