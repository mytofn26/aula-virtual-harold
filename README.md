# Aula Virtual — Harold Parco

## Qué es esto
Un sistema simple con backend real (Python/Flask), no un solo archivo HTML:
- Login de alumnas con correo + código de acceso (por ahora tú generas el código a mano, no hay pago automático todavía)
- Página de curso protegida (solo entra quien tenga código válido)
- Panel de administración para crear y quitar accesos

## Cómo probarlo en tu computadora
1. Instala Python si no lo tienes (python.org)
2. Abre una terminal en esta carpeta
3. Ejecuta: `pip install -r requirements.txt`
4. Ejecuta: `python app.py`
5. Abre tu navegador en: http://localhost:5000

## Cómo usarlo
- **Crear acceso:** entra a `/admin` (contraseña por defecto: `harold2026` — CÁMBIALA en `app.py`), pon nombre y correo de la alumna, el sistema genera un código único. Se lo mandas por WhatsApp junto con su correo.
- **Alumna:** entra a la página principal, pone su correo + código, y ve el curso completo.

## Editar el contenido del curso
Abre `app.py`, busca `COURSE_TITLE`, `COURSE_DESC` y `LESSONS` casi al inicio del archivo, y reemplaza los videos de ejemplo por los reales (un link de YouTube "no listado" o Vimeo privado, en formato "embed").

## IMPORTANTE antes de publicarlo de verdad
1. Cambia `ADMIN_PASSWORD` en `app.py` por algo que solo tú sepas.
2. Cambia `app.secret_key` en `app.py` por un texto largo y aleatorio.
3. Esto necesita un hosting que corra Python — no es un archivo HTML suelto como la web principal. Opciones fáciles con plan gratuito para empezar: Render.com, Railway.app o PythonAnywhere.com — las tres aceptan apps Flask sin complicarse.
4. Cuando integren pagos reales (Culqi, MercadoPago), ese paso reemplaza la creación manual de accesos por una automática apenas se confirme el pago — tal cual acordamos, eso lo dejamos para el final.
