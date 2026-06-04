from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "brutalfood_secret"

DB = "restaurante.db"

def get_db():
    conn = sqlite3.connect(DB, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

# ---------------- BASE DE DATOS ----------------
def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS mesas (
        id INTEGER PRIMARY KEY,
        estado TEXT
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

    c.execute("""
    CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        precio REAL
    )
    """)

    for i in range(1, 7):
        c.execute("INSERT OR IGNORE INTO mesas VALUES (?, ?)", (i, "Libre"))

    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["user"] == "nicolasjef" and request.form["password"] == "123450808":
            session["user"] = "ok"
            return redirect("/")
        return "❌ incorrecto"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# ---------------- HOME ----------------
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
        pedidos = c.execute(
            "SELECT id, producto, precio FROM pedidos WHERE mesa_id=?",
            (m[0],)
        ).fetchall()

        total = sum([p[2] for p in pedidos])

        data.append({
            "id": m[0],
            "estado": m[1],
            "pedidos": pedidos,
            "total": total
        })

    conn.close()

    return render_template("index.html", mesas=data, menu=menu)

# ---------------- AGREGAR PEDIDO ----------------
@app.route("/ordenar/<int:mesa>/<producto>")
def ordenar(mesa, producto):
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT precio FROM menu WHERE nombre=?", (producto,))
    res = c.fetchone()

    if res:
        c.execute("""
        INSERT INTO pedidos (mesa_id, producto, precio)
        VALUES (?,?,?)
        """, (mesa, producto, res[0]))

        c.execute("UPDATE mesas SET estado=? WHERE id=?",
                  ("Ocupada", mesa))

    conn.commit()
    conn.close()

    return redirect("/")

# ---------------- CANCELAR PEDIDO ----------------
@app.route("/cancelar_pedido/<int:id>")
def cancelar_pedido(id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM pedidos WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

# ---------------- COBRAR ----------------
@app.route("/limpiar/<int:mesa>")
def limpiar(mesa):
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT SUM(precio) FROM pedidos WHERE mesa_id=?", (mesa,))
    total = c.fetchone()[0] or 0

    c.execute("""
    INSERT INTO ventas (mesa_id, total, fecha)
    VALUES (?,?,datetime('now'))
    """, (mesa, total))

    c.execute("DELETE FROM pedidos WHERE mesa_id=?", (mesa,))
    c.execute("UPDATE mesas SET estado=? WHERE id=?", ("Libre", mesa))

    conn.commit()
    conn.close()
    return redirect("/")

# ---------------- RUN (IMPORTANTE PARA CELULAR) ----------------
if __name__ == "__main__":
    print("🔥 Servidor activo")
    print("PC: http://127.0.0.1:5000/login")
    print("CELULAR: http://IP_DEL_PC:5000/login")

    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)