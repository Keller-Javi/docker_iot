from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import os, logging
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mqtt import Mqtt

import random
from datetime import datetime, timedelta

logging.basicConfig(format='%(asctime)s - CRUD - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask(__name__)

app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

# Configuración de la base de datos
app.secret_key = os.environ["FLASK_SECRET_KEY"]
app.config["MYSQL_USER"] = os.environ["MYSQL_USER"]
app.config["MYSQL_PASSWORD"] = os.environ["MYSQL_PASSWORD"]
app.config["MYSQL_DB"] = os.environ["MYSQL_DB"]
app.config["MYSQL_HOST"] = os.environ["MYSQL_HOST"]
app.config['PERMANENT_SESSION_LIFETIME']=180
mysql = MySQL(app)

# Configuración del broker MQTT
app.config['MQTT_BROKER_PORT'] = int(os.environ['PUERTO_MQTTS'])
app.config['MQTT_BROKER_URL'] = os.environ['DOMINIO']
app.config['MQTT_USERNAME'] = os.environ['MQTT_USR']
app.config['MQTT_PASSWORD'] = os.environ['MQTT_PASS']
app.config['MQTT_KEEPALIVE'] = 720  # Tiempo de keepalive
app.config['MQTT_TLS_ENABLED'] = True  # Habilita TLS si es necesario

import ssl
app.config['MQTT_TLS_VERSION'] = ssl.PROTOCOL_TLSv1_2

mqtt = Mqtt(app)

# rutas

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    """Registrar usuario"""
    if request.method == "POST":
        if not request.form.get("usuario"):
            flash("El campo usuario es oblicatorio", "danger")
            return redirect(url_for('login'))
        elif not request.form.get("password"):
            flash("El campo contraseña es oblicatorio", "danger")
            return redirect(url_for('login'))

        try:
            passhash=generate_password_hash(request.form.get("password"), method='scrypt', salt_length=16)
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO usuarios (usuario, hash) VALUES (%s,%s)", (request.form.get("usuario"), passhash[17:]))
            if mysql.connection.affected_rows():
                flash('Se agregó un usuario')  # usa sesión
                logging.info("se agregó un usuario")
            mysql.connection.commit()

            session.permanent = True
            session["user_id"]=request.form.get("usuario")
            session["id"] = cur.lastrowid  # Guardar el ID del usuario en la sesión

            logging.info("se registró un usuario correctamente")
            return redirect(url_for('index'))
        except Exception as e:
            logging.error("Error al registrar el usuario: {}".format(e))
            flash('Ya existe este usuario')
            return redirect(url_for('registrar'))

    return render_template('registrar.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not request.form.get("usuario"):
            flash("El campo usuario es oblicatorio", "danger")
            return redirect(url_for('login'))
        elif not request.form.get("password"):
            flash("El campo contraseña es oblicatorio", "danger")
            return redirect(url_for('login'))

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios WHERE usuario LIKE %s", (request.form.get("usuario"),))
        rows=cur.fetchone()
        if(rows):
            if (check_password_hash('scrypt:32768:8:1$' + rows[2],request.form.get("password"))):
                session.permanent = True
                session["user_id"]=request.form.get("usuario")
                session["id"] = rows[0]  # Guardar el ID del usuario en la sesión
                logging.info("se autenticó correctamente")
                return redirect(url_for('index'))
            else:
                flash('usuario o contraseña incorrecto')
                logging.info("usuario o contraseña incorrecto")
                return redirect(url_for('login'))
    return render_template('login.html')

def generar_temperaturas(n=24, temp_inicio=23, delta_max=2, limites=(21, 30)):
    temps = [temp_inicio]
    for _ in range(1, n):
        delta = random.uniform(-delta_max, delta_max)
        nueva = temps[-1] + delta
        # Limitar al rango deseado
        nueva = max(limites[0], min(limites[1], nueva))
        temps.append(round(nueva, 1))
    return temps

@app.route('/', methods=['GET', 'POST'])
@require_login
def index():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM dispositivos WHERE usuario = %s', (session["id"],))
    nodos = cur.fetchall()
    cur.close()

    # Generar etiquetas (por ejemplo, últimas 24 horas cada hora)
    now = datetime.now()
    labels = [(now - timedelta(hours=i)).strftime("%H:%M") for i in reversed(range(24))]
    # Valores aleatorios entre 15°C y 30°C
    data = generar_temperaturas()

    if request.method == 'POST':
            logging.info("recibió una petición POST")
            nodo = request.form['nodo']
            comando = request.form['comando']

            logging.info("comando: {}".format(comando))
            if comando == 'destello':
                mqtt.publish(topic=f'{nodo}/destello', payload='destello')
        
            if comando == 'setpoint':
                setpoint = request.form['valor_setpoint']
                if not setpoint:
                    flash("El campo Valor Setpoint es oblicatorio", "danger")
                    return redirect(url_for('index'))
                mqtt.publish(topic=f'{nodo}/setpoint', payload=int(setpoint))
            
            flash('Enviado "{comando}" a {nodo}'.format(comando=comando, nodo=nodo))
            return redirect(url_for('index'))
    logging.info(nodos)
    return render_template('index.html', nodos=nodos, dark_mode=session.get("darkmode", False), labels=labels, data=data)

@app.route("/logout")
@require_login
def logout():
    session.clear()
    logging.info("el usuario {} cerró su sesión".format(session.get("user_id")))
    return redirect(url_for('index'))

@app.route("/darkmode", methods=["POST"])
@require_login
def darkmode():
    """Cambiar el modo de visualización"""
    if request.method == "POST":
        if session.get("darkmode") is None:
            session["darkmode"] = True
        else:
            session["darkmode"] = not session["darkmode"]
        logging.info("cambió el modo de visualización a {}".format(session.get("darkmode")))
    return redirect(request.referrer or url_for('index'))

@app.route("/add_node", methods=["GET","POST"])
@require_login
def add_node():
    if request.method == "POST":
        if not request.form.get("id_disp"):
            return "el campo ID del dispositivo es oblicatorio"
        elif not request.form.get("name_disp"):
            return "el campo Nombre del dispositivo es oblicatorio"

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM usuarios WHERE usuario LIKE %s", (session["user_id"],))
            user=cur.fetchone()

            cur.execute("INSERT INTO dispositivos (id, nombre, usuario) VALUES (%s,%s,%s)", 
                            (request.form.get("id_disp"), request.form.get("name_disp"), user[0]))
            if mysql.connection.affected_rows():
                    flash('Se agregó un dispositivo')
                    logging.info("se agregó un dispositivo")
            mysql.connection.commit()
            return redirect(url_for('index'))
        except:
            logging.error("Error al agregar el dispositivo")
            flash('Error al agregar el dispositivo')
    return render_template('add_node.html', nodo=[], dark_mode=session.get("darkmode", False))

@app.route('/borrar_nodo/<string:id>', methods = ['GET'])
@require_login
def borrar_nodo(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM dispositivos WHERE id = %s', (id,))
        if mysql.connection.affected_rows():
            flash('Se eliminó un contacto')
            logging.info("se eliminó un contacto")
            mysql.connection.commit()
    except:
        logging.error("Error al eliminar el nodo")
        flash('Error al eliminar el nodo')
    return redirect(url_for('index'))

@app.route('/editar/<id>', methods = ['GET'])
@require_login
def conseguir_contacto(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM contactos WHERE id = %s', (id,))
    datos = cur.fetchone()
    logging.info(datos)
    return render_template('editar-contacto.html', contacto = datos, dark_mode=session.get("darkmode", False))

@app.route('/actualizar/<id>', methods=['POST'])
@require_login
def actualizar_contacto(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        tel = request.form['tel']
        email = request.form['email']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE contactos SET nombre=%s, tel=%s, email=%s WHERE id=%s", (nombre, tel, email, id))
    if mysql.connection.affected_rows():
        flash('Se actualizó un contacto')  # usa sesión
        logging.info("se actualizó un contacto")
        mysql.connection.commit()
    return redirect(url_for('index'))