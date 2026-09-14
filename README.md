# Campus Parking — Demo web integrada (Sprints 1, 2 y 3)

Esta carpeta contiene una aplicación web que une en una sola interfaz todo lo
construido en los 3 sprints, para poder mostrarla en vivo en la sustentación
en lugar de solo scripts de terminal.

No reemplaza los módulos por sprint (siguen en `app/`, cada uno documentado
con su historia de usuario): esta app (`flask_app.py`) solo les pone una
interfaz web encima, usando Flask porque el Sprint 2 fue el primero en pedir
explícitamente una pantalla (M2-03, M2-04) — ver la justificación completa
del stack en el documento técnico, sección de Sprint 2.

## Cómo levantarla (la noche antes o el mismo día de la sustentación)

1. Necesitan **Python 3.10 o superior** instalado.
2. Abran una terminal dentro de esta carpeta (`web_app/`).
3. Instalen las dependencias (una sola vez, necesita internet):
   ```bash
   pip install -r requirements.txt
   ```
4. Arranquen el servidor:
   ```bash
   python3 flask_app.py
   ```
5. Abran el navegador en: **http://127.0.0.1:5050**

No necesita internet para funcionar una vez instaladas las dependencias:
Bootstrap está empaquetado localmente en `static/vendor/`, así que la demo
funciona aunque el salón de clase no tenga wifi.

## Qué mostrar en la sustentación (sugerido, ~5 minutos)

1. **Inicio (`/`)** — panel general con las 3 zonas y accesos a cada sprint.
2. **Registro / QR (`/registro`)** — registrar un vehículo de ejemplo y
   mostrar el QR generado (M1-01).
3. **Vigilante (`/vigilante`)** — escribir esa misma placa, elegir zona, y
   mostrar el semáforo VÁLIDO con el tiempo de validación (M1-02/M1-03).
4. **Panel de Cupos (`/panel`)** — dejarlo abierto en una pestaña aparte
   mientras registran entradas en otra, para que se vea actualizarse solo
   cada 4 segundos (M2-02/M2-03/M2-06).
5. **Reservar (`/reservar`)** — crear una reserva para otra placa con hora de
   inicio = ahora mismo, y luego volver a "Vigilante" con esa placa para
   mostrar que el sistema detecta la reserva vigente al escanear (M3-01/M3-03).
6. **Reporte de seguridad (`/reporte-seguridad`)** — mostrar que la placa
   registrada sin reserva sí aparece en el reporte, y la que sí tenía
   reserva no aparece.

## Capturas de respaldo

En `screenshots/` hay capturas reales de cada pantalla (por si el proyector
falla o quieren pegarlas también en las diapositivas). Los nombres coinciden
con las rutas: `home.png`, `registro.png`, `vigilante_resultado.png`,
`panel_datos.png`, `reservar.png`, `mis_reservas.png`, `historial.png`,
`reporte_seguridad.png`, `disponibilidad.png`, `mi_qr.png`.

## Reiniciar la base de datos antes de la demo en vivo

Los datos de prueba que usé para las capturas (placas TST111, TST222)
quedaron en `data/campus_parking.db` si la carpeta existe. Para empezar la
demo desde cero:
```bash
rm -rf data
```
La próxima vez que arranquen `flask_app.py` se recrea automáticamente, con
las 3 zonas (Zona A, B, C) ya configuradas con aforo de 100 cada una.

## Estructura

```
web_app/
├── flask_app.py          <- servidor web (integra todo)
├── app/                  <- lógica de cada sprint (sin cambios de fondo)
│   ├── db.py              Base de datos SQLite (usuarios, registros, zonas, reservas)
│   ├── qr_generator.py    M1-01
│   ├── validator.py       M1-02 / M1-03 (+ integra M3-03)
│   ├── entry_log.py       M1-03
│   ├── contingency.py     M1-04
│   ├── zones.py           M2-01 / M2-02 / M2-05 / M2-06
│   └── reservations.py    M3-01 / M3-02 / M3-04 / M3-05
├── templates/             <- páginas HTML (Flask/Jinja)
├── static/                <- CSS propio + Bootstrap empaquetado localmente
├── screenshots/           <- capturas de respaldo
└── tests/
    ├── checklist_prueba_porteria.md   <- M1-05 (checklist para prueba real)
    └── medicion_tiempo.py             <- M1-05 (medición de latencia de software)
```
