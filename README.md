# Aula Virtual — Harold Parco

## Qué es esto
Un sistema con backend real (Python/Flask):
- **Página pública de inscripción** (`/inscribirme`) — el cliente ve el curso y el precio, escanea tu QR de pago, y sube su captura como comprobante
- **Panel de administración** (`/admin`) — ves las solicitudes pendientes con su comprobante, apruebas con un clic (se genera el código automático) o rechazas
- **Login de alumnas** con correo + código de acceso
- **Página de curso protegida** — solo entra quien tenga código válido

## El flujo completo
1. Cliente entra a `/inscribirme`, ve el precio y tu QR, paga, sube su captura y manda el formulario
2. Te llega la solicitud a `/admin` con su nombre, correo, WhatsApp y la foto del comprobante
3. Revisas la captura — si el pago es real, tocas "Aprobar y generar código"
4. El sistema genera un código único y te lo muestra en pantalla
5. Le mandas ese código a la alumna por WhatsApp (esto sigue siendo manual, a propósito — la próxima fase es automatizarlo con una pasarela real)
6. La alumna entra a la web principal con su correo + código, y ve el curso

## Antes de usarlo, reemplaza tu QR real
Pon tu imagen de QR de Yape/Plin en:
```
static/uploads/qr-pago.png
```
(tiene que llamarse exactamente así, o cambia el nombre en `app.py` línea con `QR_IMAGE`)

## Cómo probarlo en tu computadora
1. Instala Python si no lo tienes (python.org)
2. Abre una terminal en esta carpeta
3. Ejecuta: `pip install -r requirements.txt`
4. Ejecuta: `python app.py`
5. Abre tu navegador en: http://localhost:5000/inscribirme (vista del cliente) y http://localhost:5000/admin (tu panel)

## Editar el contenido del curso
Abre `app.py`, busca `COURSE_TITLE`, `COURSE_DESC`, `COURSE_PRICE`, `PAYMENT_WHATSAPP` y `LESSONS` casi al inicio del archivo, y reemplaza por los datos reales.

## IMPORTANTE antes de publicarlo de verdad
1. Cambia `ADMIN_PASSWORD` en `app.py` por algo que solo tú sepas.
2. Cambia `app.secret_key` en `app.py` por un texto largo y aleatorio.
3. Sube tu QR real a `static/uploads/qr-pago.png`.
4. Esto necesita un hosting que corra Python — no es un archivo HTML suelto. Opciones fáciles con plan gratuito: Render.com, Railway.app o PythonAnywhere.com.
5. Cuando integren una pasarela de pago real (Culqi, MercadoPago), esa integración reemplaza el paso de "aprobar manualmente" por uno automático apenas se confirme el pago — eso queda para el final, como acordamos.
