# Campus Parking

Sistema de control de entradas y disponibilidad de cupos para un parqueadero
institucional. Reemplaza el registro manual en portería por verificación
digital con código QR, muestra los cupos disponibles por zona en tiempo real,
y permite reservar un cupo por franja horaria.

## Funcionalidades

- **Registro y QR** — cada vehículo se registra una vez (con su correo
  institucional) y recibe un código QR único, vinculado a su placa, que usa
  para entrar y salir.
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
  libera automáticamente para otro vehículo.
- **Recordatorios por correo (M3-06)** — un proceso en segundo plano envía un
  recordatorio por SMTP 15 minutos antes de que inicie la reserva.
- **Historial y reportes** — historial de entradas/salidas exportable en
  CSV, y un reporte de los vehículos que ingresaron sin una reserva vigente.
- **Estado del sistema** — pantalla que muestra la configuración SMTP y el
  estado del scheduler (página *Sistema*).
- **Protección CSRF** — todos los formularios exigen un token de sesión.

## Cómo funciona, en conjunto

1. El usuario se registra una sola vez (nombre, placa, correo, rol) y
   descarga su QR.
2. Cada vez que pasa por portería, el vigilante escanea ese mismo QR: el
   sistema decide solo si es una entrada o una salida, según cuál fue el
   último movimiento registrado para esa placa (no hay que elegirlo a mano).
3. Cada entrada válida descuenta un cupo de la zona elegida; cada salida lo
   libera. El panel y la vista del conductor reflejan ese cambio al momento.
4. Si el vehículo tenía una reserva vigente para esa hora, el sistema la
   detecta y la marca como usada en el mismo escaneo.
5. Todo movimiento queda guardado y es consultable después, por placa o por
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
| `SMTP_HOST` | Servidor SMTP de salida | `smtp.gmail.com` |
| `SMTP_PORT` | Puerto SMTP | `587` |
| `SMTP_USER` / `SMTP_PASSWORD` | Credenciales SMTP (requeridas para M3-06) | vacío |
| `FROM_EMAIL` / `FROM_NAME` | Remitente de los recordatorios | `noreply@...` |

### Activar los recordatorios por correo (M3-06)

1. Copia `.env.example` a `.env` (`Copy-Item .env.example .env` en Windows).
2. Con Gmail, genera una **contraseña de aplicación**: activa la *Verificación en
   2 pasos* en `myaccount.google.com/security` y crea una app en
   `myaccount.google.com/apppasswords` (16 caracteres, con espacios). No uses tu
   contraseña normal.
3. Pon tu correo en `SMTP_USER` y `FROM_EMAIL`, y la contraseña de aplicación en
   `SMTP_PASSWORD`.
4. Reinicia el servidor y verifica en **Sistema → Estado del sistema** →
   **Probar conexión SMTP**: debe salir *“Conexión SMTP exitosa”*.

Desde ese momento, el scheduler (cada minuto) envía un recordatorio 15 minutos
antes del inicio de cada reserva, al correo registrado del conductor.

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
├── flask_app.py          <- servidor web, rutas y protección CSRF
├── .env.example          <- plantilla de configuración por variables de entorno
├── app/
│   ├── db.py               Base de datos SQLite (usuarios, registros, zonas, reservas)
│   ├── qr_generator.py     Registro de usuarios y generación del QR
│   ├── validator.py        Validación del escaneo en portería
│   ├── entry_log.py        Registro de entradas/salidas y listado de vehículos
│   ├── contingency.py      Validación manual por placa (modo sin red)
│   ├── zones.py            Zonas, aforo y ocupación en tiempo real
│   ├── reservations.py     Reservas, no-show, historial, reportes y recordatorios
│   ├── email_service.py    Envío de correos por SMTP (M3-06)
│   ├── email_templates.py  Plantillas HTML/texto de los recordatorios
│   ├── scheduler.py        Tareas en segundo plano (APScheduler)
│   └── csrf.py             Token CSRF por sesión
├── templates/             <- páginas HTML (base, macros y por módulo)
├── static/                <- estilos propios + Bootstrap empaquetado localmente
├── docs_operacion/        <- entregables de operación (guias, retrospectiva, sponsor)
├── scripts/               <- utilidades (evidencia de los 5 días del sponsor)
├── screenshots/           <- capturas de referencia de cada pantalla
└── tests/
    ├── test_*.py            52 pruebas con pytest (BD y tiempo aislados)
    ├── conftest.py          fixtures (BD temporal, reloj fijo, cliente web)
    ├── checklist_prueba_porteria.md
    └── medicion_tiempo.py   medición de latencia de validación
```

## Entregables y evidencia (Taller 3)

- **Operación:** `docs_operacion/guia_vigilantes.md`,
  `docs_operacion/comunicado_conductores.md`,
  `docs_operacion/guia_historial_seguridad.md`,
  `docs_operacion/retrospectiva_final.md`.
- **Validación del sponsor:** `docs_operacion/checklist_validacion_sponsor_5_dias.md`
  (generada con `python scripts/generar_evidencia_5_dias.py`).
- **Screenshots de cada pantalla:** `screenshots/`.
- **Pruebas:** 52 pruebas en verde — `python -m pytest tests -q`.