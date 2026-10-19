# Campus Parking

Sistema de control de entradas y disponibilidad de cupos para un parqueadero
institucional. Reemplaza el registro manual en portería por verificación
digital con código QR, muestra los cupos disponibles por zona en tiempo real,
y permite reservar un cupo por franja horaria.

---

## 🚨 IMPORTANT: Email Configuration Issue

**If emails are NOT arriving:**

The Gmail App Password in `.env.example` (`ntgd zypa afbf rygn`) **is NOT working**.

**YOU MUST generate your own Gmail App Password:**

1. Go to: https://myaccount.google.com/apppasswords
2. Generate a NEW 16-character password
3. Use it in your configuration:
   ```bash
   EMAIL_ADDRESS="your-email@gmail.com"
   EMAIL_PASSWORD="your-16-char-password"
   ```

See **`EMAIL_PROBLEM_DIAGNOSIS.md`** for complete instructions.

---

## Funcionalidades

- **Registro y QR** — cada vehículo se registra una vez (con su correo
  institucional) y recibe un código QR único, vinculado a su placa, que usa
  para entrar y salir.
- **🔐 Login por correo** — sistema de autenticación basado en email. Los
  usuarios inician sesión con su correo institucional para acceder a su
  dashboard personal y crear reservas.
- **👤 Dashboard de usuario** — panel personalizado que muestra información
  del vehículo, disponibilidad en tiempo real, accesos rápidos y últimas
  reservas.
- **Validación en portería** — el vigilante escanea (o escribe) la placa y el
  sistema responde de inmediato si el ingreso es válido.
- **Modo de contingencia** — si falla la red o el lector, se puede validar la
  placa manualmente contra una copia local de los vehículos autorizados.
- **Panel de cupos en tiempo real** — muestra, por zona, cuántos cupos hay
  libres, con alerta cuando una zona se llena. Se actualiza solo cada pocos
  segundos, sin recargar la página.
- **Disponibilidad para el conductor** — la misma información del panel,
  pero en una vista pública pensada para consultarse antes de entrar.
- **Reservas por horario** — un usuario puede reservar su cupo con
  anticipación; si no llega dentro de los primeros 15 minutos, la reserva se
  libera automáticamente para otro vehículo. Requiere autenticación.
- **📧 Confirmación por correo** — al crear una reserva, el usuario recibe
  inmediatamente un correo de confirmación con todos los detalles en formato
  HTML profesional.
- **⏰ Recordatorios por correo (M3-06)** — un proceso en segundo plano envía un
  recordatorio por SMTP 15 minutos antes de que inicie la reserva.
- **Historial y reportes** — historial de entradas/salidas exportable en
  CSV, y un reporte de los vehículos que ingresaron sin una reserva vigente.
- **Vehículos registrados** — lista de todos los usuarios con su estado
  actual (dentro/fuera del campus) y acceso directo a su QR y su historial.
  Desde ahí también se puede dar de baja un vehículo (ya no podrá ingresar) o
  reactivarlo. No se permite dar de baja a un vehículo que está dentro del
  campus: primero debe registrarse su salida.
- **Cancelar reservas** — desde "Mis reservas" el usuario cancela una reserva
  activa y el cupo de esa franja queda libre.
- **Medición del tiempo de ingreso** — pantalla con un cronómetro para medir
  cada ingreso en portería (o registrar un tiempo a mano). Calcula el
  promedio por día y dice si se cumple la meta de aceptación: 3 minutos o
  menos durante 5 días hábiles consecutivos, con al menos 20 vehículos por
  día. Las mediciones se pueden descargar en CSV.
- **Estado del sistema** — pantalla que muestra la configuración SMTP y el
  estado del scheduler (página *Sistema*).
- **Protección CSRF** — todos los formularios exigen un token de sesión.

## Cómo funciona, en conjunto

1. El usuario se registra una sola vez (nombre, placa, correo, rol) y
   descarga su QR.
2. **El usuario inicia sesión** con su correo institucional para acceder a su
   dashboard y funciones personalizadas.
3. **Desde el dashboard**, el usuario puede:
   - Ver disponibilidad en tiempo real de todas las zonas
   - Crear nuevas reservas de parqueadero
   - Ver el historial de sus reservas
   - Descargar su código QR
4. **Al crear una reserva**, recibe dos emails automáticos:
   - Email de confirmación inmediata con los detalles de la reserva
   - Email de recordatorio 15 minutos antes del inicio
5. Cada vez que pasa por portería, el vigilante escanea el QR: el
   sistema decide solo si es una entrada o una salida, según cuál fue el
   último movimiento registrado para esa placa (no hay que elegirlo a mano).
6. Cada entrada válida descuenta un cupo de la zona elegida; cada salida lo
   libera. El panel y la vista del conductor reflejan ese cambio al momento.
7. Si el vehículo tenía una reserva vigente para esa hora, el sistema la
   detecta y la marca como usada en el mismo escaneo.
8. Todo movimiento queda guardado y es consultable después, por placa o por
   fecha, desde el historial y los reportes.

## Instalación y ejecución

Requiere Python 3.10 o superior.

```bash
pip install -r requirements.txt
python flask_app.py
```

Luego abre el navegador en **http://127.0.0.1:5050**

No necesita internet para funcionar una vez instaladas las dependencias:
Bootstrap está empaquetado localmente en `static/vendor/`.

### Modo desarrollo (recarga automática)

```bash
# Windows PowerShell
$env:FLASK_DEBUG="1"; python flask_app.py
# Linux / macOS
FLASK_DEBUG=1 python flask_app.py
```

## Configuración con variables de entorno

Copia `.env.example` a `.env` y ajusta los valores. El archivo `.env` no se
sube al repositorio.

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `SECRET_KEY` | Clave de sesión (genera una larga y aleatoria) | `campus-parking-demo` |
| `CSRF_OFF` | `1` desactiva la protección CSRF (solo pruebas) | `0` |
| `FLASK_DEBUG` | `1` activa el modo debug del servidor | `0` |
| `PORT` | Puerto del servidor web | `5050` |
| **`EMAIL_ADDRESS`** | **📧 Email de Gmail para enviar notificaciones (RECOMENDADO)** | vacío |
| **`EMAIL_PASSWORD`** | **🔑 Contraseña de aplicación de Gmail (16 caracteres)** | vacío |
| `SMTP_HOST` | Servidor SMTP de salida (Gmail por defecto) | `smtp.gmail.com` |
| `SMTP_PORT` | Puerto SMTP | `587` |
| `SMTP_USER` / `SMTP_PASSWORD` | Credenciales SMTP alternativas (EMAIL_ADDRESS toma prioridad) | vacío |
| `FROM_EMAIL` / `FROM_NAME` | Remitente de los correos | `EMAIL_ADDRESS` / `Campus Parking` |

### 🔐 Activar el Login y las Notificaciones por Correo

El sistema ahora requiere que los usuarios inicien sesión para crear reservas y envía dos tipos de correos automáticos.

#### 1. Configurar Gmail para envío de correos

1. **Activa la Verificación en 2 pasos** en tu cuenta de Gmail:
   - Ve a: https://myaccount.google.com/security
   - Sigue los pasos para activar la verificación

2. **Genera una contraseña de aplicación**:
   - Ve a: https://myaccount.google.com/apppasswords
   - Crea una contraseña para “Mail” u “Otra aplicación”
   - Copia la contraseña de 16 caracteres (ej: `abcd efgh ijkl mnop`)

3. **Configura las variables de entorno**:
   
   Opción A - Usando `.env` file (Recomendado):
   ```bash
   # Copia el archivo de ejemplo
   Copy-Item .env.example .env  # Windows
   # cp .env.example .env        # Linux/Mac

   # Edita .env y actualiza:
   EMAIL_ADDRESS=tu-correo@gmail.com
   EMAIL_PASSWORD=tu-contrasena-16-caracteres
   SECRET_KEY=genera-una-clave-secreta-aqui
   ```

   Opción B - Variables de entorno del sistema (Temporal):
   ```bash
   # Windows PowerShell
   $env:EMAIL_ADDRESS=”tu-correo@gmail.com”
   $env:EMAIL_PASSWORD=”tu-contrasena-16-caracteres”
   $env:SECRET_KEY=”clave-secreta”

   # Linux / macOS
   export EMAIL_ADDRESS=”tu-correo@gmail.com”
   export EMAIL_PASSWORD=”tu-contrasena-16-caracteres”
   export SECRET_KEY=”clave-secreta”
   ```

4. **Inicia el servidor**:
   ```bash
   python flask_app.py
   ```

5. **Verifica la configuración**:
   - Abre: http://127.0.0.1:5050/sistema
   - Click en **”Probar conexión SMTP”**
   - Debe mostrar: *”Conexión SMTP exitosa”*

#### 2. Usar el Sistema

1. **Registrar un vehículo** (si aún no lo has hecho):
   - Ve a: http://127.0.0.1:5050/registro
   - Completa el formulario con tu **correo electrónico válido**
   - Descarga tu código QR

2. **Iniciar sesión**:
   - Ve a: http://127.0.0.1:5050/login
   - Ingresa tu correo electrónico
   - Serás redirigido a tu dashboard personal

3. **Crear una reserva**:
   - Desde el dashboard, click en **”Reservar Cupo”**
   - Selecciona zona, fecha y horario
   - Click en “Reservar”
   - ✅ **Recibirás inmediatamente un correo de confirmación**
   - ⏰ **15 minutos antes del inicio, recibirás un correo de recordatorio**

#### Tipos de Correos Automáticos

**IMPORTANTE: Recibirás 2 correos por cada reserva:**

1. **✅ Confirmación de Reserva** (INMEDIATO - se envía AL MOMENTO de crear la reserva):
   - Se envía INSTANTÁNEAMENTE cuando haces click en "Reservar"
   - NO tienes que esperar
   - Recibes el correo en menos de 5 segundos
   - Incluye todos los detalles: zona, fecha, horario
   - Plantilla HTML profesional con tema verde
   - Asunto: "Confirmacion de Reserva - Campus Parking"

2. **⏰ Recordatorio de Reserva** (15 minutos antes del inicio):
   - Se envía automáticamente 15 min antes del inicio
   - Recuerda llegar a tiempo
   - Plantilla HTML profesional con tema púrpura
   - Asunto: "Recordatorio: Tu reserva de parqueadero inicia en 15 minutos"
   - Procesado por el scheduler en segundo plano (cada 1 minuto)

**Flujo de Emails:**
```
Crear Reserva → Email Confirmación (inmediato) → Email Recordatorio (15 min antes)
    ↓                    ↓                              ↓
  Ahora            En 2-5 segundos                  15 min antes
```

## Reiniciar los datos

Para volver a empezar sin los datos de prueba:
```bash
rm -rf data
```
Al arrancar de nuevo se recrea solo, con 3 zonas ya configuradas (100 cupos
cada una).

## Estructura

```
campus-parking/
├── flask_app.py            <- servidor web, rutas, autenticación y protección CSRF
├── .env.example            <- plantilla de configuración (incluye EMAIL_ADDRESS/EMAIL_PASSWORD)
├── LOGIN_AND_EMAIL_SETUP.md <- guía completa de configuración de login y emails
├── app/
│   ├── db.py               Base de datos SQLite (usuarios, registros, zonas, reservas)
│   ├── qr_generator.py     Registro de usuarios y generación del QR
│   ├── validator.py        Validación del escaneo en portería
│   ├── entry_log.py        Registro de entradas/salidas y listado de vehículos
│   ├── contingency.py      Validación manual por placa (modo sin red)
│   ├── zones.py            Zonas, aforo y ocupación en tiempo real
│   ├── reservations.py     Reservas, cancelación, confirmación, recordatorios (M3-06)
│   ├── aceptacion.py       Mediciones de ingreso y dictamen de aceptación (5 días ≤ 3 min)
│   ├── email_service.py    Envío de correos por SMTP (confirmación + recordatorios)
│   ├── email_templates.py  Plantillas HTML/texto (confirmación + recordatorios)
│   ├── scheduler.py        Tareas en segundo plano (APScheduler)
│   └── csrf.py             Token CSRF por sesión
├── templates/              <- páginas HTML (base, macros y por módulo)
│   ├── login.html          <- página de inicio de sesión (NUEVA)
│   ├── dashboard.html      <- dashboard personal del usuario (NUEVA)
│   ├── reservar.html       <- actualizada: usa usuario logueado
│   └── base.html           <- actualizada: menú con login/logout
├── static/                 <- estilos propios + Bootstrap empaquetado localmente
├── docs_operacion/         <- entregables de operación (guias, retrospectiva, sponsor)
├── scripts/                <- utilidades (evidencia de los 5 días del sponsor)
├── screenshots/            <- capturas de referencia de cada pantalla
└── tests/
    ├── test_*.py            52 pruebas con pytest (BD y tiempo aislados)
    ├── conftest.py          fixtures (BD temporal, reloj fijo, cliente web)
    ├── checklist_prueba_porteria.md
    └── medicion_tiempo.py   medición de latencia de validación
```

## 🔧 Solución de Problemas (Troubleshooting)

### Error al iniciar sesión: "Internal Server Error"

**Síntomas:**
- Al hacer login con tu email, aparece "Internal Server Error"
- El dashboard no carga correctamente

**Solución:**
1. **Verifica que el servidor esté usando las variables de entorno:**
   ```bash
   # Asegúrate de ejecutar con las variables:
   EMAIL_ADDRESS="tu-correo@gmail.com" EMAIL_PASSWORD="tu-password" SECRET_KEY="tu-secret" py flask_app.py
   ```

2. **Verifica que el usuario esté registrado con un email válido:**
   - Ve a http://127.0.0.1:5050/registro
   - Regístrate con tu correo electrónico
   - Luego intenta hacer login con ese mismo correo

3. **Verifica los logs del servidor:**
   - Revisa la salida de la consola donde corre Flask
   - Busca errores relacionados con la base de datos

### Error: ".env file: 'utf-8' codec can't decode byte 0xff"

**Síntoma:**
- El servidor no inicia y muestra error de encoding

**Solución:**
- Este error es normal y no afecta el funcionamiento
- El sistema usa las variables de entorno del sistema en su lugar
- Para evitar el warning, elimina el archivo `.env` si existe:
  ```bash
  rm -f .env
  ```

### No recibo emails de confirmación o recordatorio

**Pasos para diagnosticar:**

1. **Revisa los LOGS del servidor en la consola:**
   - Busca líneas que digan `[CONFIRMACION]` o `[OK] Email enviado`
   - Si ves `[CONFIRMACION] Email de confirmacion enviado exitosamente` → el email SÍ se envió
   - Si ves `[CONFIRMACION] Error: No se pudo enviar` → hay un problema de configuración

2. **Verifica la configuración SMTP:**
   - Ve a: http://127.0.0.1:5050/sistema
   - Click en "Probar conexión SMTP"
   - Debe decir "Conexión SMTP exitosa"
   - Si falla, verifica que EMAIL_ADDRESS y EMAIL_PASSWORD estén bien

3. **Verifica las variables de entorno:**
   ```bash
   # Linux/Mac
   echo $EMAIL_ADDRESS
   echo $EMAIL_PASSWORD
   
   # Windows PowerShell
   echo $env:EMAIL_ADDRESS
   echo $env:EMAIL_PASSWORD
   ```

4. **Revisa la carpeta de SPAM** en tu correo (Gmail a veces filtra emails automáticos)

5. **Verifica que el usuario tenga un email registrado:**
   ```bash
   py -c "from app.db import get_conn; conn = get_conn(); print(conn.execute('SELECT placa, email FROM usuarios').fetchall()); conn.close()"
   ```

6. **Prueba manual de envío de email:**
   ```bash
   EMAIL_ADDRESS="tu-correo@gmail.com" EMAIL_PASSWORD="tu-password" py -c "
   from app.email_service import enviar_email
   resultado = enviar_email('destino@gmail.com', 'Test', 'Mensaje de prueba', '<h1>Test HTML</h1>')
   print('Email enviado!' if resultado else 'Error al enviar')
   "
   ```

**Tiempos de entrega esperados:**
- **Confirmación:** 2-10 segundos después de crear la reserva
- **Recordatorio:** Exactamente 15 minutos antes del inicio (±2 min ventana)

## Entregables y evidencia (Taller 3)

- **Operación:** `docs_operacion/guia_vigilantes.md`,
  `docs_operacion/comunicado_conductores.md`,
  `docs_operacion/guia_historial_seguridad.md`,
  `docs_operacion/retrospectiva_final.md`.
- **Validación del sponsor:** `docs_operacion/checklist_validacion_sponsor_5_dias.md`
  (generada con `python scripts/generar_evidencia_5_dias.py`).
- **Screenshots de cada pantalla:** `screenshots/`.
- **Pruebas:** 52 pruebas en verde — `python -m pytest tests -q`.