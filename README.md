# Diabetes App (GlucoIntel)

Pequeña aplicación Django que usa un modelo de clasificación para estimar el riesgo de diabetes (usando los metadatos del dataset Pima). El frontend está pensado para un despliegue moderno (Bootstrap, WhiteNoise) y el backend ya incluye autenticación, restablecimiento de contraseña y envío de correo gracias a `django.contrib.auth`.

## Requisitos

- Python 3.11+.
- Postgres (local o gestionado) para datos persistentes de usuarios.
- Un servidor SMTP (o `EMAIL_BACKEND=console`, útil en desarrollo).

## Desarrollo local

1. Crea y activa un entorno virtual:
   ```bash
   python -m venv .venv
   .venv/Scripts/Activate.ps1   # PowerShell
   ```
2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Duplica `.env.example` y ajusta los valores sensibles. Asegúrate de definir al menos `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` y, si usas Postgres local, `DATABASE_URL`.
4. Aplica migraciones y crea usuarios:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser  # opcional
   ```
5. (Opcional) Recopila archivos estáticos mientras pruebas localmente:
   ```bash
   python manage.py collectstatic --noinput
   ```
6. Arranca el servidor:
   ```bash
   python manage.py runserver
   ```

> En ausencia de `DATABASE_URL`, Django crea un `db.sqlite3` en la raíz para desarrollo rápido.

## Despliegue en Render (u otro host similar)

1. **Base de datos persistente:** Render permite añadir un servicio PostgreSQL gestionado; crea el servicio y copia la cadena de conexión (`postgres://usuario:clave@host:puerto/nombre`). En el panel web del servicio Django, añade las siguientes variables de entorno:
   - `DATABASE_URL` (la URL completa de Postgres).
   - `SECRET_KEY` (valor secreto por entorno).
   - `DEBUG=False`.
   - `ALLOWED_HOSTS=tu-app.onrender.com` (y otros dominios que uses).
   - `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`/`EMAIL_USE_SSL`, `DEFAULT_FROM_EMAIL` según tu proveedor SMTP.
   - `PASSWORD_RESET_DOMAIN_OVERRIDE` y `PASSWORD_RESET_PROTOCOL_OVERRIDE` (por ejemplo `diabetes-app-eby0.onrender.com` y `https`).
2. **Comandos de construcción/arranque:**
   - Build Command: `./build.sh` (instala dependencias, ejecuta `collectstatic` y ejecuta migraciones).
   - Start Command: `gunicorn config.wsgi --workers 3 --bind 0.0.0.0:$PORT` (ya definido en `Procfile`).
3. Con `DATABASE_URL` en el entorno, `config/settings.py` usará Postgres gracias a `dj_database_url`. Eso garantiza que usuarios, contraseñas y registros sobrevivan los redeploys.

## Consejos rápidos

- No subas `db.sqlite3` al repositorio; el archivo solo sirve para pruebas locales y ya está ignorado por `.gitignore`.
- Si no tienes un SMTP real aún, puedes dejar `ALLOW_CONSOLE_EMAIL=True` o usar `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` en desarrollo, pero asegúrate de proveer un backend SMTP en producción para restablecer contraseñas.
- Asegúrate de que `MODEL_PATH` y `SCALER_PATH` (`diabetes_app/model.pkl`, `diabetes_app/scaler.pkl`) existen antes de ejecutar predicciones. Puedes generar ambos con `python train_model.py --csv ruta/al/dataset.csv`.
- **Script de preparación:** ejecuta `scripts/bootstrap.sh` (añade permisos con `chmod +x scripts/bootstrap.sh` si es necesario) después de copiar `.env.example` a `.env` y rellenar los valores. El script carga esas variables, corre `python manage.py migrate` y `python manage.py collectstatic --noinput`, dejando el entorno listo para pruebas o el deploy.
