from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from models import Pedidos, Venta, db, Cliente, Usuario  
from config import DevelopmentConfig
import os
import forms

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app.config.from_object('config.DevelopmentConfig') 

csrf = CSRFProtect(app)


db.init_app(app)
with app.app_context():
    db.create_all()
    PEDIDOS_FILE = "pedidos.txt"

login_manager = LoginManager(app)
login_manager.login_view = "login"  

@app.route("/", methods=["GET", "POST"])

def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = Usuario.query.filter_by(username=username).first()  # Buscar en la base de datos

        if user and user.check_password(password):  # Verificar la contraseña
            login_user(user)
            flash("Login exitoso", "success")
            return redirect(url_for("index"))  # Redirigir a la página principal
        else:
            flash("Usuario o contraseña incorrectos", "danger")

    return render_template("login.html")

# Cargar el usuario para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    create_form = forms.ClientesForm(request.form)
    pedidos = cargar_pedidos()
    ventas = Venta.query.all()
    
    print("Pedidos:", pedidos)  # Depuración
    print("Ventas:", ventas)    # Depuración

    ventas_agrupadas = {}
    for venta in ventas:
        if venta.cliente.nombre not in ventas_agrupadas:
            ventas_agrupadas[venta.cliente.nombre] = {
                'cliente': venta.cliente,
                'total': 0.0
            }
        ventas_agrupadas[venta.cliente.nombre]['total'] += venta.montoTotal

    ventas_totales = [{
        'nombre': datos['cliente'].nombre,
        'total': datos['total']
    } for datos in ventas_agrupadas.values()]

    return render_template("index.html", pedidos=pedidos, form=create_form, ventas=ventas_totales)


def guardar_pedido(pedido):
    """Guarda un pedido en un archivo de texto"""
    with open(PEDIDOS_FILE, "a") as f:
        f.write(f"{pedido['nombre']}|{pedido['direccion']}|{pedido['telefono']}|{pedido['size']}|{','.join(pedido['ingredientes'])}|{pedido['num_pizzas']}|{pedido['subtotal']}\n")

def cargar_pedidos():
    """Carga los pedidos desde el archivo con validación para evitar errores."""
    pedidos = []
    if os.path.exists(PEDIDOS_FILE):
        with open(PEDIDOS_FILE, "r") as f:
            for linea in f:
                datos = linea.strip().split("|")
                
                if len(datos) != 7:
                    print(f"Error: Línea mal formada en pedidos.txt -> {linea.strip()}")
                    continue  

                try:
                    pedidos.append({
                        "nombre": datos[0],
                        "direccion": datos[1],
                        "telefono": datos[2],
                        "size": datos[3],
                        "ingredientes": datos[4].split(",") if datos[4] else [],
                        "num_pizzas": int(datos[5]),
                        "subtotal": float(datos[6])
                    })
                except ValueError as e:
                    print(f"Error al convertir datos: {e}, en línea: {linea.strip()}")
                    continue  

    return pedidos

@app.route('/pedido', methods=['GET', 'POST'])
def pedido():
    if request.method == 'POST':
        nombre = request.form['nombre']
        direccion = request.form['direccion']
        telefono = request.form['telefono']
        size = request.form['size']
        ingredientes = request.form.getlist('ingredientes')
        num_pizzas = int(request.form['num_pizzas'])
        session['cliente'] = {
            'nombre': nombre,
            'direccion': direccion,
            'telefono': telefono
        }

        precios = {"chica": 40, "mediana": 80, "grande": 120}
        precio_unitario = precios.get(size, 40)
        precio_ingrediente = 10
        subtotal = (precio_unitario + (precio_ingrediente * len(ingredientes))) * num_pizzas

        pedido = {
            "nombre": nombre,
            "direccion": direccion,
            "telefono": telefono,
            "size": size,
            "ingredientes": ingredientes,
            "num_pizzas": num_pizzas,
            "subtotal": subtotal
        }
        guardar_pedido(pedido)
        
        flash('Pedido agregado correctamente', 'success')
        
        return redirect(url_for('index'))

    return render_template('index.html')


@app.route('/terminar', methods=['POST'])
def terminar_pedidos():
    """Transfiere los pedidos del archivo a la base de datos y limpia el archivo."""
    pedidos = cargar_pedidos()

    if not pedidos:
        return redirect(url_for('index'))

    for pedido in pedidos:
        cliente = Cliente.query.filter_by(nombre=pedido["nombre"], telefono=pedido["telefono"]).first()
        if not cliente:
            cliente = Cliente(nombre=pedido["nombre"], direccion=pedido["direccion"], telefono=pedido["telefono"])
            db.session.add(cliente)
            db.session.commit()
        nuevo_pedido = Pedidos(
            tamanio=pedido["size"],
            ingredientes=", ".join(pedido["ingredientes"]),
            cantidad=pedido["num_pizzas"]
        )
        db.session.add(nuevo_pedido)
        db.session.commit()

        precios = {"chica": 40, "mediana": 80, "grande": 120}
        precio_unitario = precios.get(pedido["size"], 40)
        precio_ingrediente = 10
        subtotal = (precio_unitario + (precio_ingrediente * len(pedido["ingredientes"]))) * pedido["num_pizzas"]

        nueva_venta = Venta(
            idPedido=nuevo_pedido.id,  
            idCliente=cliente.id,      
            montoTotal=subtotal,
            size=pedido["size"],
            ingredientes=", ".join(pedido["ingredientes"]),
            num_pizzas=pedido["num_pizzas"],
            subtotal=subtotal
        )
        db.session.add(nueva_venta)

    db.session.commit()
    session.pop('cliente', None)
    flash('Pedido se agregado correctamente', 'success')


    open(PEDIDOS_FILE, "w").close()  

    return redirect(url_for('index'))


@app.route('/quitar_pedido/<int:index>', methods=['POST'])
def quitar_pedido(index):
    with open("pedidos.txt", "r") as file:
        pedidos = file.readlines()
    
    if 0 <= index < len(pedidos):
        del pedidos[index]  

        with open("pedidos.txt", "w") as file:
            file.writelines(pedidos)  

    return redirect(url_for('index'))  

if __name__ == '__main__':
    app.run(debug=True)