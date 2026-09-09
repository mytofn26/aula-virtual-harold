# Aula Virtual — Harold Parco (modelo de suscripción mensual)

## Qué es esto
Sistema de membresía mensual con backend real (Python/Flask + Culqi):
- **Página de suscripción** (`/suscribirme`) — la clienta paga con tarjeta (Culqi, cobro automático mensual)
- **Login** con correo + código de acceso
- **Curso protegido** — muestra las clases subidas, solo si la suscripción está activa
- **Panel de administración** (`/admin`) — subes clases nuevas cada mes, ves quién está suscrita y su estado
- **Webhook de Culqi** — si un cobro falla o la alumna cancela, el acceso se desactiva solo

## Lo que falta para que funcione con dinero real
Este proyecto está construido y probado en todas sus partes EXCEPTO la conexión final con Culqi,
porque todavía no tenemos las llaves reales. Faltan estos pasos, en orden:

### 1. Crear cuenta en Culqi
Ve a culqi.com y crea una cuenta. Para PROBAR (sandbox) no necesitas RUC ni verificación de negocio —
solo para cuando quieran cobrar dinero real.

### 2. Sacar tus llaves de prueba
En tu Panel de Culqi, busca "Llaves de integración" (Desarrollo > API Keys). Vas a ver:
- Una llave pública: `pk_test_...`
- Una llave secreta: `sk_test_...`

### 3. Crear el plan mensual
En tu Panel de Culqi, ve a Suscripciones > Planes > Crear plan. Define el monto (ej: S/50) y que sea mensual.
Te va a dar un ID que empieza con `pln_test_...`

### 4. Pegar las 3 llaves en el código
Abre `app.py`, busca esta sección casi al inicio:
```python
CULQI_PUBLIC_KEY = "pk_test_TU_LLAVE_PUBLICA_AQUI"
CULQI_SECRET_KEY = "sk_test_TU_LLAVE_SECRETA_AQUI"
CULQI_PLAN_ID = "pln_test_TU_PLAN_AQUI"
```
Reemplaza cada uno por el valor real que te dio Culqi.

### 5. Configurar el Webhook (para que se entere de pagos fallidos o cancelaciones)
En tu Panel de Culqi, busca "Webhooks" y agrega esta URL (una vez que esté publicado en Render):
```
https://tu-app.onrender.com/webhook/culqi
```

### 6. Probar con tarjetas de prueba
Culqi tiene tarjetas de prueba que simulan pagos exitosos y fallidos sin mover dinero real —
las encuentras en su documentación bajo "Tarjetas de prueba". Prueba el flujo completo con esas antes de pasar a producción.

## Cómo probarlo en tu computadora
1. Instala Python si no lo tienes (python.org)
2. Abre una terminal en esta carpeta
3. Ejecuta: `pip install -r requirements.txt`
4. Ejecuta: `python app.py`
5. Abre tu navegador en: http://localhost:5000/suscribirme (vista de venta) y http://localhost:5000/admin (tu panel)

## Cómo usarlo día a día
- **Subir clase nueva del mes:** entra a `/admin`, en "Subir clase nueva" pon el título y el link del video (YouTube no listado o Vimeo, en formato "embed"). Aparece automático para todas las suscriptoras activas.
- **Ver quién está suscrita:** la tabla de abajo en `/admin` muestra nombre, correo, código, y si está Activa o no.
- **Acceso manual (cortesía, casos especiales):** el formulario "Crear acceso manual" — no pasa por Culqi, solo para excepciones.

## IMPORTANTE antes de publicarlo con dinero real
1. Cambia `ADMIN_PASSWORD` en `app.py` por algo que solo tú sepas.
2. Cambia `app.secret_key` en `app.py` por un texto largo y aleatorio.
3. Cuando termines de probar con llaves `pk_test_`/`sk_test_`, Culqi requiere que verifiques tu negocio (RUC, cuenta bancaria) para darte las llaves de PRODUCCIÓN (`pk_live_`/`sk_live_`) — ahí sí empieza a llegar dinero real a la cuenta.
4. Sube estos cambios con git add / commit / push como siempre — Render los despliega solo.
