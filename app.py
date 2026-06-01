from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "brutalfood_secret"

DB = "restaurante.db"


# =========================
# CONEXIÓN DB
# =========================

def get_db():

    conn = sqlite3.connect(DB, timeout=10)

    conn.execute("PRAGMA journal_mode=WAL")

    return conn


# =========================
# CREAR DB
# =========================

def init_db():

    conn = get_db()
    c = conn.cursor()

    # MESAS
    c.execute("""
    CREATE TABLE IF NOT EXISTS mesas (
        id INTEGER PRIMARY KEY,
        estado TEXT
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

    # MENU
    c.execute("""
    CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
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

    # CREAR 6 MESAS
    for i in range(1, 7):

        c.execute("""
        INSERT OR IGNORE INTO mesas (id, estado)
        VALUES (?,?)
        """, (
            i,
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

        # USUARIO FIJO
        if usuario == "nicolasjef" and password == "123450808":

            session["user"] = usuario

            return redirect("/")

        return "Usuario o contraseña incorrectos"

    return render_template("login.html")


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
        """, (mesa[0],)).fetchall()

        total = sum([pedido[3] for pedido in pedidos])

        mesas_data.append({
            "id": mesa[0],
            "estado": mesa[1],
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

    if "user" not in session:
        return redirect("/login")

    nombre = request.form["nombre"]
    precio = request.form["precio"]

    conn = get_db()
    c = conn.cursor()

    c.execute("""
    INSERT INTO menu (nombre, precio)
    VALUES (?,?)
    """, (
        nombre,
        float(precio)
    ))

    conn.commit()
    conn.close()

    return redirect("/")


# =========================
# ELIMINAR PRODUCTO
# =========================

@app.route("/eliminar_producto/<int:id>")
def eliminar_producto(id):

    if "user" not in session:
        return redirect("/login")

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
# AGREGAR PEDIDO
# =========================

@app.route("/ordenar/<int:mesa>/<int:producto_id>")
def ordenar(mesa, producto_id):

    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    producto = c.execute("""
    SELECT nombre, precio
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
            producto[0],
            producto[1]
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

    if "user" not in session:
        return redirect("/login")

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

    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    total = c.execute("""
    SELECT SUM(precio)
    FROM pedidos
    WHERE mesa_id=?
    """, (mesa,)).fetchone()[0]

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
    SELECT SUM(total)
    FROM ventas
    """).fetchone()[0]

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
    app.run(debug=True)