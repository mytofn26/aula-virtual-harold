import sqlite3
import secrets
import string
import os
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session, url_for, flash

app = Flask(__name__)
app.secret_key = "cambia-esta-clave-en-produccion-por-una-larga-y-aleatoria"

DB_PATH = "aula.db"
ADMIN_PASSWORD = "harold2026"  # cámbiala antes de publicar
UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "pdf"}

# ==== CONTENIDO DEL CURSO (edita esto directamente) ====
COURSE_TITLE = "Curso 5 días: Sistema Dual"
COURSE_DESC = "Polygel y builder gel: cánulas de moldes duales, dual sandwich y extensiones híbridas. Desde cero, sin experiencia previa."
COURSE_PRICE = "S/680"
PAYMENT_WHATSAPP = "51936268510"
QR_IMAGE = "uploads/qr-pago.png"  # reemplaza este archivo por tu QR real de Yape/Plin
LESSONS = [
    {"title": "Clase 1 — Introducción y materiales", "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
    {"title": "Clase 2 — Preparación de la uña natural", "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
    {"title": "Clase 3 — Moldes duales, primera aplicación", "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
    {"title": "Clase 4 — Dual sandwich y extensiones híbridas", "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
    {"title": "Clase 5 — Acabado, limado y sellado final", "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
]
TRUST_POINTS = [
    "+600 alumnas graduadas",
    "Embajador de Cherimoya Perú",
    "Certificación oficial incluida",
]
TESTIMONIAL = {
    "quote": "Excelente atención y servicio. El ambiente es súper relajante y el personal muy profesional. Totalmente recomendado.",
    "author": "Angeles Principe Noel · Reseña en Google",
}
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pending_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            whatsapp TEXT NOT NULL,
            proof_file TEXT,
            requested_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendiente'
        )
    """)
    conn.commit()
    conn.close()
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


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


@app.route("/inscribirme", methods=["GET", "POST"])
def inscribirme():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        whatsapp = request.form.get("whatsapp", "").strip()
        file = request.files.get("proof")

        if not (name and email and whatsapp):
            flash("Completa todos los campos.")
            return render_template("inscribirme.html", title=COURSE_TITLE, desc=COURSE_DESC, price=COURSE_PRICE,
                                    qr_image=QR_IMAGE, whatsapp=PAYMENT_WHATSAPP, lessons=LESSONS,
                                    trust_points=TRUST_POINTS, testimonial=TESTIMONIAL)

        proof_filename = None
        if file and file.filename:
            ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            if ext in ALLOWED_EXT:
                proof_filename = secure_filename(f"{secrets.token_hex(6)}_{file.filename}")
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], proof_filename))

        conn = get_db()
        conn.execute(
            "INSERT INTO pending_requests (name, email, whatsapp, proof_file, requested_at, status) VALUES (?, ?, ?, ?, ?, 'pendiente')",
            (name, email, whatsapp, proof_filename, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        return render_template("gracias.html", whatsapp=PAYMENT_WHATSAPP)

    return render_template("inscribirme.html", title=COURSE_TITLE, desc=COURSE_DESC, price=COURSE_PRICE,
                            qr_image=QR_IMAGE, whatsapp=PAYMENT_WHATSAPP, lessons=LESSONS,
                            trust_points=TRUST_POINTS, testimonial=TESTIMONIAL)


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
    pending = conn.execute("SELECT * FROM pending_requests WHERE status = 'pendiente' ORDER BY requested_at DESC").fetchall()
    conn.close()
    return render_template("admin_dashboard.html", students=students, pending=pending, course_title=COURSE_TITLE)


@app.route("/admin/approve/<int:request_id>", methods=["POST"])
@admin_required
def admin_approve(request_id):
    conn = get_db()
    req = conn.execute("SELECT * FROM pending_requests WHERE id = ?", (request_id,)).fetchone()
    if req:
        code = generate_code()
        try:
            conn.execute(
                "INSERT INTO students (name, email, access_code, enrolled_at) VALUES (?, ?, ?, ?)",
                (req["name"], req["email"], code, datetime.now().isoformat())
            )
            conn.execute("UPDATE pending_requests SET status = 'aprobado' WHERE id = ?", (request_id,))
            conn.commit()
            flash(f"Aprobado: {req['name']} ({req['email']}) — código: {code}. Mándaselo por WhatsApp: {req['whatsapp']}")
        except sqlite3.IntegrityError:
            flash("Ese correo ya tenía una cuenta creada.")
    conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/reject/<int:request_id>", methods=["POST"])
@admin_required
def admin_reject(request_id):
    conn = get_db()
    conn.execute("UPDATE pending_requests SET status = 'rechazado' WHERE id = ?", (request_id,))
    conn.commit()
    conn.close()
    flash("Solicitud rechazada.")
    return redirect(url_for("admin_dashboard"))


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
