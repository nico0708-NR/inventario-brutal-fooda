from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "brutalfood_secret"

DB = "restaurante.db"

# ================= DB =================
def get_db():
    conn = sqlite3.connect(DB, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS mesas (
        id INTEGER PRIMARY KEY,
        nombre TEXT,
        estado TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        precio REAL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mesa_id INTEGER,
        producto TEXT,
        precio REAL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mesa_id INTEGER,
        total REAL,
        fecha TEXT
    )
    """)

    for i in range(1, 7):
        c.execute("""
        INSERT OR IGNORE INTO mesas (id, nombre, estado)
        VALUES (?, ?, ?)
        """, (i, f"Mesa {i}", "Libre"))

    conn.commit()
    conn.close()

init_db()

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["user"] == "nicolasjef" and request.form["password"] == "123450808":
            session["user"] = "ok"
            return redirect("/")
        return "Login incorrecto"
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= HOME =================
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    mesas = c.execute("SELECT * FROM mesas").fetchall()
    menu = c.execute("SELECT id, nombre, precio FROM menu").fetchall()

    data = []

    for m in mesas:
        pedidos = c.execute("""
        SELECT id, producto, precio
        FROM pedidos
        WHERE mesa_id=?
        """, (m[0],)).fetchall()

        total = sum([p[2] for p in pedidos]) if pedidos else 0

        data.append({
            "id": m[0],
            "nombre": m[1],
            "estado": m[2],
            "pedidos": pedidos,
            "total": total
        })

    conn.close()

    return render_template("index.html", mesas=data, menu=menu)


# ================= PRODUCTOS =================
@app.route("/agregar_producto", methods=["POST"])
def agregar_producto():
    if "user" not in session:
        return redirect("/login")

    nombre = request.form["nombre"]
    precio = request.form["precio"]

    conn = get_db()
    c = conn.cursor()

    c.execute("INSERT INTO menu (nombre, precio) VALUES (?,?)",
              (nombre, float(precio)))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/eliminar_producto/<int:id>")
def eliminar_producto(id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    c.execute("DELETE FROM menu WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/")


# ================= PEDIDOS =================
@app.route("/ordenar/<int:mesa>/<int:producto_id>")
def ordenar(mesa, producto_id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    producto = c.execute("""
    SELECT nombre, precio FROM menu WHERE id=?
    """, (producto_id,)).fetchone()

    if producto:
        c.execute("""
        INSERT INTO pedidos (mesa_id, producto, precio)
        VALUES (?,?,?)
        """, (mesa, producto[0], producto[1]))

        c.execute("UPDATE mesas SET estado=? WHERE id=?",
                  ("Ocupada", mesa))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/cancelar_pedido/<int:id>")
def cancelar_pedido(id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    c.execute("DELETE FROM pedidos WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/")


# ================= COBRAR =================
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
    """, (mesa,)).fetchone()[0] or 0

    c.execute("""
    INSERT INTO ventas (mesa_id, total, fecha)
    VALUES (?,?,datetime('now'))
    """, (mesa, total))

    c.execute("DELETE FROM pedidos WHERE mesa_id=?", (mesa,))
    c.execute("UPDATE mesas SET estado=? WHERE id=?", ("Libre", mesa))

    conn.commit()
    conn.close()

    return redirect("/")


# ================= VENTAS =================
@app.route("/ventas")
def ventas():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    ventas = c.execute("""
    SELECT id, mesa_id, total, fecha
    FROM ventas
    ORDER BY id DESC
    """).fetchall()

    total_general = c.execute("""
    SELECT SUM(total) FROM ventas
    """).fetchone()[0] or 0

    conn.close()

    return render_template("ventas.html",
                           ventas=ventas,
                           total_general=total_general)


# ================= DASHBOARD CHART =================
@app.route("/dashboard_data")
def dashboard_data():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    data = c.execute("""
    SELECT fecha, total FROM ventas
    ORDER BY id ASC
    """).fetchall()

    conn.close()

    return {
        "fechas": [d[0] for d in data],
        "totales": [d[1] for d in data]
    }


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)