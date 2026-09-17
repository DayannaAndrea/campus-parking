# Campus Parking

Sistema de control de entradas y disponibilidad de cupos para un parqueadero
institucional. Reemplaza el registro manual en portería por verificación
digital con código QR, muestra los cupos disponibles por zona en tiempo real,
y permite reservar un cupo por franja horaria.

## Funcionalidades

- **Registro y QR** — cada vehículo se registra una vez y recibe un código
  QR único, vinculado a su placa, que usa para entrar y salir.
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
- **Historial y reportes** — historial de entradas/salidas exportable en
  CSV, y un reporte de los vehículos que ingresaron sin una reserva vigente.
- **Vehículos registrados** — lista de todos los usuarios con su estado
  actual (dentro/fuera del campus) y acceso directo a su QR y su historial.

## Cómo funciona, en conjunto

1. El usuario se registra una sola vez y descarga su QR.
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
python3 flask_app.py
```

Luego abre el navegador en **http://127.0.0.1:5050**

No necesita internet para funcionar una vez instaladas las dependencias:
Bootstrap está empaquetado localmente en `static/vendor/`.

## Reiniciar los datos

Para volver a empezar sin los datos de prueba:
```bash
rm -rf data
```
Al arrancar de nuevo se recrea solo, con 3 zonas ya configuradas (100 cupos
cada una).

## Estructura

```
web_app/
├── flask_app.py          <- servidor web y rutas
├── app/
│   ├── db.py               Base de datos SQLite (usuarios, registros, zonas, reservas)
│   ├── qr_generator.py     Registro de usuarios y generación del QR
│   ├── validator.py        Validación del escaneo en portería
│   ├── entry_log.py        Registro de entradas/salidas y listado de vehículos
│   ├── contingency.py      Validación manual por placa (modo sin red)
│   ├── zones.py            Zonas, aforo y ocupación en tiempo real
│   └── reservations.py     Reservas, liberación por no-show, historial y reportes
├── templates/             <- páginas HTML
├── static/                <- estilos propios + Bootstrap empaquetado localmente
├── screenshots/           <- capturas de referencia de cada pantalla
└── tests/
    ├── checklist_prueba_porteria.md   <- checklist para medir el tiempo real de ingreso
    └── medicion_tiempo.py             <- script de medición de latencia
```
