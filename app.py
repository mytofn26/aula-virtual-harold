import sqlite3
import secrets
import string
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, session, url_for, flash

app = Flask(__name__)
app.secret_key = "cambia-esta-clave-en-produccion-por-una-larga-y-aleatoria"

DB_PATH = "aula.db"
ADMIN_PASSWORD = "harold2026"  # cámbiala antes de publicar

# ==== CONTENIDO DEL CURSO (edita esto directamente) ====
COURSE_TITLE = "Curso 5 días: Sistema Dual"
COURSE_DESC = "Polygel y builder gel: cánulas de moldes duales, dual sandwich y extensiones híbridas. Desde cero, sin experiencia previa."
LESSONS = [
    {"title": "Clase 1 — Introducción y materiales", "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
    {"title": "Clase 2 — Preparación de la uña natural", "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
    {"title": "Clase 3 — Moldes duales, primera aplicación", "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
    {"title": "Clase 4 — Dual sandwich y extensiones híbridas", "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
    {"title": "Clase 5 — Acabado, limado y sellado final", "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
]
# =========================================================


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            access_code TEXT NOT NULL UNIQUE,
            enrolled_at TEXT NOT NULL,
            last_login TEXT
        )
    """)
    conn.commit()
    conn.close()


def generate_code(length=8):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper


def student_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("student_email"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        code = request.form.get("code", "").strip().upper()
        conn = get_db()
        student = conn.execute(
            "SELECT * FROM students WHERE email = ? AND access_code = ?",
            (email, code)
        ).fetchone()
        if student:
            conn.execute(
                "UPDATE students SET last_login = ? WHERE id = ?",
                (datetime.now().isoformat(), student["id"])
            )
            conn.commit()
            conn.close()
            session["student_email"] = email
            session["student_name"] = student["name"]
            return redirect(url_for("curso"))
        conn.close()
        flash("Correo o código incorrecto. Verifica con quien te lo entregó.")
    return render_template("login.html")


@app.route("/curso")
@student_required
def curso():
    return render_template(
        "course.html",
        title=COURSE_TITLE,
        desc=COURSE_DESC,
        lessons=LESSONS,
        student_name=session.get("student_name"),
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Contraseña de administrador incorrecta.")
    return render_template("admin_login.html")


@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin_dashboard():
    conn = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        if name and email:
            code = generate_code()
            try:
                conn.execute(
                    "INSERT INTO students (name, email, access_code, enrolled_at) VALUES (?, ?, ?, ?)",
                    (name, email, code, datetime.now().isoformat())
                )
                conn.commit()
                flash(f"Acceso creado para {name} ({email}) — código: {code}")
            except sqlite3.IntegrityError:
                flash("Ese correo ya tiene una cuenta registrada.")
    students = conn.execute("SELECT * FROM students ORDER BY enrolled_at DESC").fetchall()
    conn.close()
    return render_template("admin_dashboard.html", students=students, course_title=COURSE_TITLE)


@app.route("/admin/remove/<int:student_id>", methods=["POST"])
@admin_required
def admin_remove(student_id):
    conn = get_db()
    conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()
    flash("Acceso revocado.")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_login"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
