from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "brutalfood_secret"

DB = "restaurante.db"


# =========================
# CONEXIÓN DB
# =========================

def get_db():

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    return conn


# =========================
# CREAR DB
# =========================

def init_db():

    conn = get_db()
    c = conn.cursor()

    # USUARIOS
    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        password TEXT
    )
    """)

    # MESAS
    c.execute("""
    CREATE TABLE IF NOT EXISTS mesas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        estado TEXT
    )
    """)

    # MENU
    c.execute("""
    CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        precio REAL
    )
    """)

    # PEDIDOS
    c.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mesa_id INTEGER,
        producto TEXT,
        precio REAL
    )
    """)

    # VENTAS
    c.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mesa_id INTEGER,
        total REAL,
        fecha TEXT
    )
    """)

    # ADMIN
    admin = c.execute("""
    SELECT *
    FROM usuarios
    WHERE usuario=?
    """, ("admin",)).fetchone()

    if not admin:

        password_hash = generate_password_hash("123456")

        c.execute("""
        INSERT INTO usuarios (usuario, password)
        VALUES (?,?)
        """, (
            "admin",
            password_hash
        ))

    # MESAS INICIALES
    mesas = c.execute("""
    SELECT COUNT(*) as total
    FROM mesas
    """).fetchone()["total"]

    if mesas == 0:

        for i in range(1, 7):

            c.execute("""
            INSERT INTO mesas (nombre, estado)
            VALUES (?,?)
            """, (
                f"Mesa {i}",
                "Libre"
            ))

    conn.commit()
    conn.close()


init_db()


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form["user"]
        password = request.form["password"]

        conn = get_db()
        c = conn.cursor()

        user = c.execute("""
        SELECT *
        FROM usuarios
        WHERE usuario=?
        """, (usuario,)).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user"] = usuario

            return redirect("/")

        return "Usuario o contraseña incorrecta"

    return render_template("login.html")


# =========================
# REGISTRO
# =========================

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        usuario = request.form["user"]
        password = request.form["password"]

        password_hash = generate_password_hash(password)

        conn = get_db()
        c = conn.cursor()

        try:

            c.execute("""
            INSERT INTO usuarios (usuario, password)
            VALUES (?,?)
            """, (
                usuario,
                password_hash
            ))

            conn.commit()

        except:
            return "Ese usuario ya existe"

        conn.close()

        return redirect("/login")

    return render_template("registro.html")


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================
# HOME
# =========================

@app.route("/")
def home():

    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    mesas = c.execute("""
    SELECT *
    FROM mesas
    """).fetchall()

    menu = c.execute("""
    SELECT *
    FROM menu
    """).fetchall()

    mesas_data = []

    for mesa in mesas:

        pedidos = c.execute("""
        SELECT *
        FROM pedidos
        WHERE mesa_id=?
        """, (mesa["id"],)).fetchall()

        total = sum([p["precio"] for p in pedidos])

        mesas_data.append({
            "id": mesa["id"],
            "nombre": mesa["nombre"],
            "estado": mesa["estado"],
            "pedidos": pedidos,
            "total": total
        })

    conn.close()

    return render_template(
        "index.html",
        mesas=mesas_data,
        menu=menu
    )


# =========================
# AGREGAR PRODUCTO
# =========================

@app.route("/agregar_producto", methods=["POST"])
def agregar_producto():

    nombre = request.form["nombre"]
    precio = request.form["precio"]

    conn = get_db()
    c = conn.cursor()

    c.execute("""
    INSERT INTO menu (nombre, precio)
    VALUES (?,?)
    """, (
        nombre,
        precio
    ))

    conn.commit()
    conn.close()

    return redirect("/")


# =========================
# ELIMINAR PRODUCTO
# =========================

@app.route("/eliminar_producto/<int:id>")
def eliminar_producto(id):

    conn = get_db()
    c = conn.cursor()

    c.execute("""
    DELETE FROM menu
    WHERE id=?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/")


# =========================
# AGREGAR MESA
# =========================

@app.route("/agregar_mesa", methods=["POST"])
def agregar_mesa():

    nombre = request.form["nombre"]

    conn = get_db()
    c = conn.cursor()

    c.execute("""
    INSERT INTO mesas (nombre, estado)
    VALUES (?,?)
    """, (
        nombre,
        "Libre"
    ))

    conn.commit()
    conn.close()

    return redirect("/")


# =========================
# ELIMINAR MESA
# =========================

@app.route("/eliminar_mesa/<int:id>")
def eliminar_mesa(id):

    conn = get_db()
    c = conn.cursor()

    c.execute("""
    DELETE FROM mesas
    WHERE id=?
    """, (id,))

    c.execute("""
    DELETE FROM pedidos
    WHERE mesa_id=?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/")


# =========================
# AGREGAR PEDIDO
# =========================

@app.route("/ordenar/<int:mesa>/<int:producto_id>")
def ordenar(mesa, producto_id):

    conn = get_db()
    c = conn.cursor()

    producto = c.execute("""
    SELECT *
    FROM menu
    WHERE id=?
    """, (producto_id,)).fetchone()

    if producto:

        c.execute("""
        INSERT INTO pedidos (
            mesa_id,
            producto,
            precio
        )
        VALUES (?,?,?)
        """, (
            mesa,
            producto["nombre"],
            producto["precio"]
        ))

        c.execute("""
        UPDATE mesas
        SET estado=?
        WHERE id=?
        """, (
            "Ocupada",
            mesa
        ))

    conn.commit()
    conn.close()

    return redirect("/")


# =========================
# CANCELAR PEDIDO
# =========================

@app.route("/cancelar_pedido/<int:id>")
def cancelar_pedido(id):

    conn = get_db()
    c = conn.cursor()

    c.execute("""
    DELETE FROM pedidos
    WHERE id=?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/")


# =========================
# COBRAR MESA
# =========================

@app.route("/limpiar/<int:mesa>")
def limpiar(mesa):

    conn = get_db()
    c = conn.cursor()

    total = c.execute("""
    SELECT SUM(precio) as total
    FROM pedidos
    WHERE mesa_id=?
    """, (mesa,)).fetchone()["total"]

    if total is None:
        total = 0

    c.execute("""
    INSERT INTO ventas (
        mesa_id,
        total,
        fecha
    )
    VALUES (?, ?, datetime('now'))
    """, (
        mesa,
        total
    ))

    c.execute("""
    DELETE FROM pedidos
    WHERE mesa_id=?
    """, (mesa,))

    c.execute("""
    UPDATE mesas
    SET estado=?
    WHERE id=?
    """, (
        "Libre",
        mesa
    ))

    conn.commit()
    conn.close()

    return redirect("/")


# =========================
# VENTAS
# =========================

@app.route("/ventas")
def ventas():

    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    ventas = c.execute("""
    SELECT *
    FROM ventas
    ORDER BY id DESC
    """).fetchall()

    total_general = c.execute("""
    SELECT SUM(total) as total
    FROM ventas
    """).fetchone()["total"]

    if total_general is None:
        total_general = 0

    conn.close()

    return render_template(
        "ventas.html",
        ventas=ventas,
        total_general=total_general
    )


# =========================
# EJECUTAR
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)