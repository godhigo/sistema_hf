from flask import Flask, render_template, request, redirect, send_from_directory
import os
from db import get_connection
from datetime import date, datetime, timedelta
import uuid
from dotenv import load_dotenv

# --------------------------
# IMPORTS PARA LOGIN
# --------------------------
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,  # HTTPS
    SESSION_COOKIE_SAMESITE="Lax"
)

app.secret_key = os.getenv("FLASK_SECRET_KEY")
ADMIN_REGISTER_PASSWORD = os.getenv("ADMIN_REGISTER_PASSWORD")

# --------------------------
# CONFIGURACIÓN LOGIN
# --------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # a dónde mandar si no hay sesión

# --------------------------
# CONFIGURAR CARPETA DE FOTOS
# --------------------------
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")

# --------------------------
# RUTA PARA SERVIR IMÁGENES SUBIDAS
# --------------------------
@app.route('/uploads/<filename>')
def uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --------------------------
# MODELO USUARIO
# --------------------------
class Usuario(UserMixin):
    def __init__(self, id, nombre, email, password_hash):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.password_hash = password_hash


@login_manager.user_loader
def load_user(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()

    if usuario:
        return Usuario(**usuario)
    return None


# --------------------------
# RUTA SIGN UP (REGISTRO)
# --------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]
        telefono = request.form["telefono"]
        especialidad = request.form["especialidad"]
        foto = request.files.get("foto")  # puede venir vacío
        clave_registro = request.form["clave_registro"]

        # Validar contraseña maestra
        if clave_registro != ADMIN_REGISTER_PASSWORD:
            return render_template("signup.html", error="Clave de registro incorrecta")

        # Validar teléfono (opcional pero recomendado)
        if not telefono.isdigit() or len(telefono) != 10:
            return render_template("signup.html", error="El teléfono debe tener 10 dígitos")

        # Guardar foto si existe
        filename = None
        if foto and foto.filename:
            extension = foto.filename.split(".")[-1]
            filename = f"{uuid.uuid4()}.{extension}"  # nombre único
            foto.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        # Guardar usuario
        password_hash = generate_password_hash(password)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO usuarios (nombre, email, password_hash) VALUES (%s, %s, %s)",
            (nombre, email, password_hash)
        )
        conn.commit()

        # Guardar empleado
        cursor.execute(
            """
            INSERT INTO empleados (nombre, email, telefono, especialidad, foto)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (nombre, email, telefono, especialidad, filename)
        )
        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")


# --------------------------
# RUTA LOGIN
# --------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()

        if not usuario or not check_password_hash(usuario["password_hash"], password):
            return render_template("login.html", error="Email o contraseña incorrectos")

        user_obj = Usuario(**usuario)
        login_user(user_obj)

        return redirect("/")

    return render_template("login.html")


# --------------------------
# LOGOUT
# --------------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


# INDEX (PROTEGIDO)
@app.route('/')
@login_required
def index():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM citas WHERE fecha = CURDATE();")
    citas_dia = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM clientes;")
    clientes = cursor.fetchone()[0]

    try:
        cursor.execute("SELECT COUNT(*) FROM empleados WHERE estado = 'activo';")
    except:
        cursor.execute("SELECT COUNT(*) FROM empleados;")
    empleados = cursor.fetchone()[0]

    try:
        cursor.execute("""
            SELECT IFNULL(SUM(total), 0)
            FROM ventas
            WHERE YEARWEEK(fecha, 1) = YEARWEEK(CURDATE(), 1);
        """)
        ventas_semana = cursor.fetchone()[0]
    except:
        ventas_semana = 0

    cursor.close()
    conn.close()

    return render_template(
        'index.html',
        citas_dia=citas_dia,
        clientes=clientes,
        empleados=empleados,
        ventas_semana=ventas_semana
    )

@app.route('/api/dashboard')
@login_required
def dashboard_data():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Ventas últimos 7 días
    cursor.execute("""
        SELECT DATE(fecha) AS dia, SUM(total) AS total
        FROM ventas
        WHERE fecha >= CURDATE() - INTERVAL 6 DAY
        GROUP BY DATE(fecha)
        ORDER BY dia
    """)
    ventas_dias = cursor.fetchall()

    # Servicios más vendidos
    cursor.execute("""
        SELECT s.nombre_servicio, COUNT(*) AS cantidad
        FROM ventas v
        JOIN servicios s ON v.id_servicio = s.id
        GROUP BY s.nombre_servicio
        ORDER BY cantidad DESC
        LIMIT 5
    """)
    servicios = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "ventas_dias": ventas_dias,
        "servicios": servicios
    }


# EMPLEADOS (PROTEGIDO)
@app.route('/empleados')
@login_required
def empleados():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM empleados ORDER BY nombre")
    empleados = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("empleados.html", empleados=empleados)


# CLIENTES (PROTEGIDO)
@app.route('/clientes')
@login_required
def clientes():
    filtro = request.args.get('nombre', '')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM clientes WHERE nombre LIKE %s", (f"%{filtro}%",))
    clientes = cursor.fetchall()

    historial = {}

    for cliente in clientes:
        cursor.execute("""
            SELECT c.fecha, c.hora, s.nombre_servicio, e.nombre AS empleado
            FROM citas c
            JOIN servicios s ON c.id_servicio = s.id
            JOIN empleados e ON c.id_empleado = e.id
            WHERE c.id_cliente = %s

            UNION

            SELECT h.fecha, h.hora, s.nombre_servicio, e.nombre AS empleado
            FROM citas_historial h
            JOIN servicios s ON h.id_servicio = s.id
            JOIN empleados e ON h.id_empleado = e.id
            WHERE h.id_cliente = %s

            ORDER BY fecha DESC, hora DESC
        """, (cliente['id'], cliente['id']))

        historial[cliente['id']] = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("clientes.html",
                           clientes=clientes,
                           historial=historial,
                           filtro=filtro)


# CITAS (PROTEGIDO)
@app.route('/citas', methods=['GET', 'POST'])
@login_required
def citas():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    fecha_str = request.form.get('fecha') or request.args.get('fecha')
    if fecha_str:
        fecha_actual = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    else:
        fecha_actual = date.today()

    cursor.execute("""
        SELECT ci.id, cl.nombre AS nombre_cliente, s.nombre_servicio,
               e.nombre AS nombre_empleado, ci.fecha, ci.hora
        FROM citas ci
        JOIN clientes cl ON ci.id_cliente = cl.id
        JOIN servicios s ON ci.id_servicio = s.id
        JOIN empleados e ON ci.id_empleado = e.id
        WHERE ci.fecha = %s
        ORDER BY ci.hora ASC
    """, (fecha_actual,))
    citas_dia = cursor.fetchall()

    cursor.execute("SELECT id, nombre FROM clientes ORDER BY nombre")
    clientes = cursor.fetchall()
    cursor.execute("SELECT id, nombre_servicio FROM servicios ORDER BY nombre_servicio")
    servicios = cursor.fetchall()
    cursor.execute("SELECT id, nombre, especialidad FROM empleados ORDER BY nombre")
    empleados = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "citas.html",
        citas_dia=citas_dia,
        clientes=clientes,
        servicios=servicios,
        empleados=empleados,
        fecha_actual=fecha_actual.strftime("%Y-%m-%d")
    )


@app.route('/agregar_cita', methods=['POST'])
@login_required
def agregar_cita():
    nombre_cliente = request.form['cliente']
    telefono = request.form['telefono']
    id_servicio = request.form['servicio']
    id_empleado = request.form['empleado']
    fecha = request.form['fecha']
    hora = request.form['hora']

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # --------------------------
    # CLIENTE
    # --------------------------
    cursor.execute(
        "SELECT id FROM clientes WHERE nombre = %s AND telefono = %s",
        (nombre_cliente, telefono)
    )
    cliente_existente = cursor.fetchone()

    if cliente_existente:
        id_cliente = cliente_existente["id"]
    else:
        cursor.execute(
            "INSERT INTO clientes (nombre, telefono) VALUES (%s, %s)",
            (nombre_cliente, telefono)
        )
        conn.commit()
        id_cliente = cursor.lastrowid

    # --------------------------
    # VALIDAR CONFLICTO CLIENTE (MISMA HORA EXACTA)
    # --------------------------
    cursor.execute("""
        SELECT id
        FROM citas
        WHERE id_cliente = %s AND fecha = %s AND hora = %s
    """, (id_cliente, fecha, hora))

    if cursor.fetchone():
        cursor.close()
        conn.close()
        return render_template(
            "mensaje.html",
            mensaje=f"⚠ El cliente '{nombre_cliente}' ya tiene una cita el {fecha} a las {hora}.",
            regresar=f"/citas?fecha={fecha}"
        )

    # --------------------------
    # OBTENER DURACIÓN DEL SERVICIO
    # --------------------------
    cursor.execute(
        "SELECT duracion FROM servicios WHERE id = %s",
        (id_servicio,)
    )
    duracion = cursor.fetchone()["duracion"]

    hora_inicio = datetime.strptime(hora, "%H:%M")
    hora_fin = hora_inicio + timedelta(minutes=duracion)

    # --------------------------
    # VALIDAR EMPALMES DEL EMPLEADO (POR RANGO)
    # --------------------------
    cursor.execute("""
        SELECT c.hora, s.duracion
        FROM citas c
        JOIN servicios s ON c.id_servicio = s.id
        WHERE c.id_empleado = %s AND c.fecha = %s
    """, (id_empleado, fecha))

    citas_empleado = cursor.fetchall()

    for c in citas_empleado:
        h_ini = datetime.strptime(str(c["hora"]), "%H:%M:%S")
        h_fin = h_ini + timedelta(minutes=c["duracion"])

        if hora_inicio < h_fin and hora_fin > h_ini:
            cursor.close()
            conn.close()
            return render_template(
                "mensaje.html",
                mensaje="⚠ El empleado ya tiene una cita que se empalma con ese horario.",
                regresar=f"/citas?fecha={fecha}"
            )

    # --------------------------
    # INSERTAR CITA
    # --------------------------
    cursor.execute("""
        INSERT INTO citas (id_cliente, id_empleado, id_servicio, fecha, hora)
        VALUES (%s, %s, %s, %s, %s)
    """, (id_cliente, id_empleado, id_servicio, fecha, hora))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(f"/citas?fecha={fecha}")

#-----------
#Editar Cita
#-----------
@app.route('/editar_cita', methods=['GET'])
@login_required
def editar_cita():
    id_cita = request.args.get('id')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtener datos de la cita
    cursor.execute("""
        SELECT * FROM citas WHERE id = %s
    """, (id_cita,))
    cita = cursor.fetchone()

    # Obtener listas
    cursor.execute("SELECT id, nombre FROM clientes ORDER BY nombre")
    clientes = cursor.fetchall()

    cursor.execute("SELECT id, nombre_servicio FROM servicios ORDER BY nombre_servicio")
    servicios = cursor.fetchall()

    cursor.execute("SELECT id, nombre FROM empleados ORDER BY nombre")
    empleados = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'editar_cita.html',
        cita=cita,
        clientes=clientes,
        servicios=servicios,
        empleados=empleados
    )

@app.route('/actualizar_cita', methods=['POST'])
@login_required
def actualizar_cita():
    id_cita = request.form['id']
    id_cliente = request.form['id_cliente']
    id_servicio = request.form['id_servicio']
    id_empleado = request.form['id_empleado']
    fecha = request.form['fecha']
    hora = request.form['hora']

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Verificar conflicto de cliente
    cursor.execute("""
        SELECT id FROM citas
        WHERE id_cliente = %s AND fecha = %s AND hora = %s AND id != %s
    """, (id_cliente, fecha, hora, id_cita))

    if cursor.fetchone():
        return render_template("mensaje.html",
                               mensaje="⚠ El cliente ya tiene una cita en ese horario.",
                               regresar=f"/editar_cita?id={id_cita}")

    # Verificar conflicto de empleado
    cursor.execute("""
        SELECT id FROM citas
        WHERE id_empleado = %s AND fecha = %s AND hora = %s AND id != %s
    """, (id_empleado, fecha, hora, id_cita))

    if cursor.fetchone():
        return render_template("mensaje.html",
                               mensaje="⚠ El empleado ya tiene una cita en ese horario.",
                               regresar=f"/editar_cita?id={id_cita}")

    # Actualizar
    cursor.execute("""
        UPDATE citas
        SET id_cliente=%s, id_servicio=%s, id_empleado=%s, fecha=%s, hora=%s
        WHERE id = %s
    """, (id_cliente, id_servicio, id_empleado, fecha, hora, id_cita))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(f"/citas?fecha={fecha}")


@app.route('/finalizar_cita', methods=['POST'])
@login_required
def finalizar_cita():
    id_cita = request.form['id_cita']

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id_cliente, id_empleado, id_servicio, fecha, hora
        FROM citas
        WHERE id = %s
    """, (id_cita,))
    cita = cursor.fetchone()

    cursor.execute("SELECT precio FROM servicios WHERE id = %s", (cita['id_servicio'],))
    precio = cursor.fetchone()['precio']

    cursor.execute("""
        INSERT INTO ventas (id_cliente, id_empleado, id_servicio, fecha, total)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        cita['id_cliente'],
        cita['id_empleado'],
        cita['id_servicio'],
        cita['fecha'],
        precio
    ))
    conn.commit()

    cursor.execute("""
        INSERT INTO citas_historial (id_cliente, id_empleado, id_servicio, fecha, hora, estado)
        SELECT id_cliente, id_empleado, id_servicio, fecha, hora, 'finalizada'
        FROM citas
        WHERE id = %s
    """, (id_cita,))
    conn.commit()

    cursor.execute("DELETE FROM citas WHERE id = %s", (id_cita,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(f"/citas?fecha={cita['fecha']}")


# VENTAS (PROTEGIDO)
@app.route('/ventas', methods=['GET', 'POST'])
@login_required
def ventas():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    filtro = request.form.get('filtro', 'dia')
    valor = request.form.get('valor_filtro', None)

    query_base = """
        SELECT v.id, c.nombre AS cliente, e.nombre AS empleado, s.nombre_servicio AS servicio, 
               v.fecha, v.total
        FROM ventas v
        JOIN clientes c ON v.id_cliente = c.id
        JOIN empleados e ON v.id_empleado = e.id
        JOIN servicios s ON v.id_servicio = s.id
    """

    filtro_query = ""
    params = ()

    if valor:
        if filtro == 'dia':
            filtro_query = "WHERE DATE(v.fecha) = %s"
            params = (valor,)
        elif filtro == 'semana':
            year, week = valor.split('-W')
            filtro_query = "WHERE YEAR(v.fecha) = %s AND WEEK(v.fecha, 1) = %s"
            params = (year, week)
        elif filtro == 'mes':
            year, month = valor.split('-')
            filtro_query = "WHERE YEAR(v.fecha) = %s AND MONTH(v.fecha) = %s"
            params = (year, month)
        elif filtro == 'ano':
            filtro_query = "WHERE YEAR(v.fecha) = %s"
            params = (valor,)
    else:
        filtro_query = "WHERE DATE(v.fecha) = CURDATE()"

    cursor.execute(f"{query_base} {filtro_query}", params)
    ventas = cursor.fetchall()

    cursor_total = conn.cursor()
    cursor_total.execute(f"SELECT IFNULL(SUM(total),0) FROM ventas v {filtro_query}", params)
    total_ganancias = cursor_total.fetchone()[0]

    cursor.close()
    cursor_total.close()
    conn.close()

    return render_template('ventas.html',
                           ventas=ventas,
                           total_ganancias=total_ganancias,
                           filtro=filtro)

# --------------------------
# MANEJO DE ERRORES
# --------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template(
        "mensaje.html",
        mensaje="❌ La página que buscas no existe",
        regresar="/"
    ), 404


@app.errorhandler(500)
def server_error(e):
    return render_template(
        "mensaje.html",
        mensaje="⚠ Ocurrió un error interno. Intenta más tarde.",
        regresar="/"
    ), 500


if __name__ == '__main__':
    app.run()
