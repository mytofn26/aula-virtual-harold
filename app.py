import sqlite3
import secrets
import string
import os
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import culqi

app = Flask(__name__)
app.secret_key = "cambia-esta-clave-en-produccion-por-una-larga-y-aleatoria"

DB_PATH = "aula.db"
ADMIN_PASSWORD = "harold2026"  # cámbiala antes de publicar
UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "pdf"}

# ==== CULQI — pega aquí tus llaves cuando las tengas (culqi.com > Llaves de integración) ====
CULQI_PUBLIC_KEY = "pk_test_TU_LLAVE_PUBLICA_AQUI"
CULQI_SECRET_KEY = "sk_test_TU_LLAVE_SECRETA_AQUI"
CULQI_PLAN_ID = "pln_test_TU_PLAN_AQUI"  # crea el plan MENSUAL una vez desde tu Panel de Culqi (CulqiPanel > Suscripciones > Planes)
culqi.private_key = CULQI_SECRET_KEY
# ============================================================================================

# ==== CONTENIDO Y MARCA (edita esto directamente) ====
COURSE_TITLE = "Academia Harold Parco"
COURSE_DESC = "Nuevas clases de técnicas de uñas cada mes: polygel, sistema dual, decoración y más."
PAYMENT_WHATSAPP = "51936268510"

# Precios — PENDIENTE: confirmar montos finales con Harold (estos son provisionales)
MONTHLY_PRICE_LABEL = "S/50"
MONTHLY_PRICE_CENTS = 5000
ANNUAL_PRICE_LABEL = "S/480"
ANNUAL_PRICE_CENTS = 48000
ANNUAL_SAVINGS_LABEL = "Ahorras S/120 vs pagar mes a mes"

# Beneficios — PENDIENTE: ajustar con datos reales que Harold confirme (horas de contenido, etc.)
BENEFITS = [
    {"icon": "🎬", "text": "Nuevas clases agregadas cada mes"},
    {"icon": "🔓", "text": "Acceso ilimitado a todo el contenido, sin pagar por curso aparte"},
    {"icon": "🏅", "text": "Certificación oficial incluida"},
    {"icon": "💬", "text": "Acompañamiento en el grupo de la comunidad"},  # PENDIENTE: crear el grupo real antes de publicar
]

GALLERY = [
    {"file": "gallery-1.jpg", "label": "Acrílico"},
    {"file": "gallery-2.jpg", "label": "Polygel"},
    {"file": "gallery-3.jpg", "label": "Sistema dual"},
    {"file": "gallery-4.jpg", "label": "Cromado"},
    {"file": "gallery-5.jpg", "label": "Técnicas mixtas"},
    {"file": "gallery-6.jpg", "label": "Pedicura"},
]

URGENCY_MESSAGE = "El precio de lanzamiento sube pronto. Suscríbete ahora y lo mantienes fijo, aunque el contenido siga creciendo."

TRUST_POINTS = [
    {"icon": "🎓", "text": "+600 alumnas graduadas"},
    {"icon": "🤝", "text": "Embajador de Cherimoya Perú"},
    {"icon": "🏅", "text": "Certificación oficial incluida"},
]
TESTIMONIALS = [
    {"quote": "Excelente atención y servicio. El ambiente es súper relajante y el personal muy profesional. Me encantó el resultado de mis uñas y el masaje fue justo lo que necesitaba. Totalmente recomendado 🙌", "author": "Angeles Principe Noel · Reseña en Google"},
    {"quote": "Excelente servicio, 10000/10.", "author": "Elizabeth Lopez Franco · Reseña en Google"},
    {"quote": "Muy buena atención, me encantó el servicio! Gracias", "author": "Daniela Loyola Parraga · Reseña en Google"},
]
# ======================================================


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            access_code TEXT NOT NULL UNIQUE,
            plan_type TEXT NOT NULL DEFAULT 'mensual',
            culqi_customer_id TEXT,
            culqi_card_id TEXT,
            culqi_subscription_id TEXT,
            culqi_charge_id TEXT,
            expires_at TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            last_login TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            video_url TEXT NOT NULL,
            thumbnail TEXT,
            added_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def generate_code(length=8):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def normalizar_youtube(url):
    """Acepta cualquier link de YouTube (normal, corto, ya-embed) y devuelve el formato embed."""
    import re
    patterns = [
        r'(?:youtube\.com/watch\?v=)([\w-]+)',
        r'(?:youtu\.be/)([\w-]+)',
        r'(?:youtube\.com/embed/)([\w-]+)',
        r'(?:youtube\.com/shorts/)([\w-]+)',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return f"https://www.youtube.com/embed/{m.group(1)}"
    return url  # si no es YouTube (ej: Vimeo), lo dejamos tal cual


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


# ==================== PÁGINA DE SUSCRIPCIÓN (venta) ====================

@app.route("/suscribirme")
def suscribirme():
    conn = get_db()
    lessons = conn.execute("SELECT * FROM lessons ORDER BY added_at DESC LIMIT 5").fetchall()
    conn.close()
    return render_template("suscribirme.html", title=COURSE_TITLE, desc=COURSE_DESC,
                            monthly_price=MONTHLY_PRICE_LABEL, annual_price=ANNUAL_PRICE_LABEL,
                            annual_regular_price=f"S/{MONTHLY_PRICE_CENTS * 12 / 100:.0f}",
                            monthly_price_cents=MONTHLY_PRICE_CENTS, annual_price_cents=ANNUAL_PRICE_CENTS,
                            annual_savings=ANNUAL_SAVINGS_LABEL, benefits=BENEFITS,
                            urgency_message=URGENCY_MESSAGE,
                            lessons=lessons, trust_points=TRUST_POINTS, testimonials=TESTIMONIALS,
                            gallery=GALLERY,
                            culqi_public_key=CULQI_PUBLIC_KEY)


@app.route("/suscribirme/procesar", methods=["POST"])
def suscribirme_procesar():
    """Recibe el token de CulqiJS (la tarjeta ya la manejó Culqi, nunca pasa por aquí).
    Si plan_type es 'mensual' -> crea una Suscripción (cobro recurrente).
    Si plan_type es 'anual' -> hace un Cargo único (cobro una sola vez, acceso por 1 año)."""
    data = request.get_json()
    token_id = data.get("token_id")
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    plan_type = data.get("plan_type", "mensual")

    if not (token_id and name and email):
        return jsonify({"ok": False, "error": "Faltan datos."}), 400

    try:
        code = generate_code()
        conn = get_db()

        if plan_type == "anual":
            charge = culqi.Charge.create({
                "amount": ANNUAL_PRICE_CENTS,
                "currency_code": "PEN",
                "email": email,
                "source_id": token_id,
                "description": f"{COURSE_TITLE} — Plan anual",
            })
            expires_at = datetime.now().replace(year=datetime.now().year + 1).isoformat()
            conn.execute(
                """INSERT INTO subscribers
                   (name, email, access_code, plan_type, culqi_charge_id, expires_at, status, created_at)
                   VALUES (?, ?, ?, 'anual', ?, ?, 'active', ?)""",
                (name, email, code, charge["id"], expires_at, datetime.now().isoformat())
            )
        else:
            first_name, *rest = name.split(" ", 1)
            last_name = rest[0] if rest else "-"

            customer = culqi.Customer.create({
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "address": "-",
                "address_city": "-",
                "country_code": "PE",
                "phone_number": "999999999",
            })
            card = culqi.Card.create({
                "customer_id": customer["id"],
                "token_id": token_id,
            })
            subscription = culqi.Subscription.create({
                "card_id": card["id"],
                "plan_id": CULQI_PLAN_ID,
                "tyc": True,
            })
            conn.execute(
                """INSERT INTO subscribers
                   (name, email, access_code, plan_type, culqi_customer_id, culqi_card_id, culqi_subscription_id, status, created_at)
                   VALUES (?, ?, ?, 'mensual', ?, ?, ?, 'active', ?)""",
                (name, email, code, customer["id"], card["id"], subscription["id"], datetime.now().isoformat())
            )

        conn.commit()
        conn.close()
        return jsonify({"ok": True, "code": code})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/webhook/culqi", methods=["POST"])
def webhook_culqi():
    """Culqi nos avisa aquí cuando algo cambia en una suscripción (cobro exitoso, fallido, cancelada)."""
    event = request.get_json(silent=True) or {}
    event_type = event.get("type", "")
    data = event.get("data", {})
    subscription_id = data.get("id") or data.get("subscription_id")

    if not subscription_id:
        return jsonify({"ok": True})

    conn = get_db()
    if "cancel" in event_type or "failed" in event_type:
        conn.execute(
            "UPDATE subscribers SET status = 'inactivo' WHERE culqi_subscription_id = ?",
            (subscription_id,)
        )
    elif "charge" in event_type or "succeeded" in event_type:
        conn.execute(
            "UPDATE subscribers SET status = 'active' WHERE culqi_subscription_id = ?",
            (subscription_id,)
        )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# ==================== LOGIN Y CURSO ====================

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        code = request.form.get("code", "").strip().upper()
        conn = get_db()
        sub = conn.execute(
            "SELECT * FROM subscribers WHERE email = ? AND access_code = ?",
            (email, code)
        ).fetchone()
        if sub and sub["status"] == "active" and (sub["plan_type"] != "anual" or sub["expires_at"] > datetime.now().isoformat()):
            conn.execute("UPDATE subscribers SET last_login = ? WHERE id = ?",
                         (datetime.now().isoformat(), sub["id"]))
            conn.commit()
            conn.close()
            session["student_email"] = email
            session["student_name"] = sub["name"]
            return redirect(url_for("curso"))
        elif sub and sub["plan_type"] == "anual" and sub["expires_at"] and sub["expires_at"] <= datetime.now().isoformat():
            conn.close()
            flash("Tu plan anual venció. Escríbenos por WhatsApp para renovarlo.", "login")
        elif sub and sub["status"] != "active":
            conn.close()
            flash("Tu suscripción no está activa (pago pendiente o cancelada). Escríbenos por WhatsApp.", "login")
        else:
            conn.close()
            flash("Correo o código incorrecto. Verifica con quien te lo entregó.", "login")
    return render_template("login.html")


@app.route("/curso")
@student_required
def curso():
    conn = get_db()
    lessons = conn.execute("SELECT * FROM lessons ORDER BY added_at DESC").fetchall()
    conn.close()
    return render_template(
        "course.html",
        title=COURSE_TITLE,
        desc=COURSE_DESC,
        lessons=lessons,
        student_name=session.get("student_name"),
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ==================== ADMIN ====================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Contraseña de administrador incorrecta.", "admin_login")
    return render_template("admin_login.html")


@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin_dashboard():
    conn = get_db()
    if request.method == "POST":
        form_type = request.form.get("form_type")
        if form_type == "lesson":
            title = request.form.get("lesson_title", "").strip()
            video_url = normalizar_youtube(request.form.get("lesson_video", "").strip())
            thumb_file = request.files.get("lesson_thumb")
            thumbnail = None
            if thumb_file and thumb_file.filename:
                ext = thumb_file.filename.rsplit(".", 1)[-1].lower() if "." in thumb_file.filename else ""
                if ext in ALLOWED_EXT:
                    thumbnail = secure_filename(f"leccion_{secrets.token_hex(6)}.{ext}")
                    thumb_file.save(os.path.join(app.config["UPLOAD_FOLDER"], thumbnail))
            if title and video_url:
                conn.execute(
                    "INSERT INTO lessons (title, video_url, thumbnail, added_at) VALUES (?, ?, ?, ?)",
                    (title, video_url, thumbnail, datetime.now().isoformat())
                )
                conn.commit()
                flash(f"Clase agregada: {title}", "admin")
        elif form_type == "manual":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            if name and email:
                code = generate_code()
                try:
                    conn.execute(
                        "INSERT INTO subscribers (name, email, access_code, status, created_at) VALUES (?, ?, ?, 'active', ?)",
                        (name, email, code, datetime.now().isoformat())
                    )
                    conn.commit()
                    flash(f"Acceso manual creado para {name} ({email}) — código: {code}", "admin")
                except sqlite3.IntegrityError:
                    flash("Ese correo ya tiene una cuenta registrada.", "admin")

    subscribers = conn.execute("SELECT * FROM subscribers ORDER BY created_at DESC").fetchall()
    lessons = conn.execute("SELECT * FROM lessons ORDER BY added_at DESC").fetchall()
    conn.close()

    ahora = datetime.now().isoformat()
    def esta_vigente(s):
        if s["status"] != "active":
            return False
        if s["plan_type"] == "anual" and s["expires_at"] and s["expires_at"] <= ahora:
            return False
        return True

    activas = [s for s in subscribers if esta_vigente(s)]
    mensuales_activas = [s for s in activas if s["plan_type"] == "mensual"]
    anuales_activas = [s for s in activas if s["plan_type"] == "anual"]
    ingreso_mensual_estimado = len(mensuales_activas) * MONTHLY_PRICE_CENTS / 100

    kpis = {
        "total_activas": len(activas),
        "mensuales": len(mensuales_activas),
        "anuales": len(anuales_activas),
        "ingreso_mensual": ingreso_mensual_estimado,
    }

    return render_template("admin_dashboard.html", subscribers=subscribers, lessons=lessons,
                            course_title=COURSE_TITLE, kpis=kpis, ahora=ahora)


@app.route("/admin/lessons/remove/<int:lesson_id>", methods=["POST"])
@admin_required
def admin_remove_lesson(lesson_id):
    conn = get_db()
    conn.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
    conn.commit()
    conn.close()
    flash("Clase eliminada.", "admin")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/remove/<int:subscriber_id>", methods=["POST"])
@admin_required
def admin_remove(subscriber_id):
    conn = get_db()
    conn.execute("DELETE FROM subscribers WHERE id = ?", (subscriber_id,))
    conn.commit()
    conn.close()
    flash("Acceso revocado.", "admin")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_login"))


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
