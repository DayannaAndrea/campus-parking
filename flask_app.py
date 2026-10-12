"""
Campus Parking — demo web integrada (Sprints 1, 2 y 3).

Une en una sola interfaz lo construido en cada sprint:
  Sprint 1 -> registro/QR, validador del vigilante, contingencia
  Sprint 2 -> zonas, panel de cupos en tiempo real, vista del conductor
  Sprint 3 -> reservas por franja, historial, reporte de seguridad

No reemplaza los módulos de cada sprint (app/qr_generator.py, validator.py,
contingency.py, zones.py, reservations.py): esta app solo les pone una
interfaz encima, tal como se explicó en la justificación del stack.
"""
import os
import sys
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv opcional: si falta, se usan las variables del entorno
    pass

from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify
from markupsafe import Markup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import get_conn, DATA_DIR  # noqa: E402
from app.qr_generator import generar_qr, placa_valida  # noqa: E402
from app.validator import escanear, validar_token  # noqa: E402
from app.entry_log import historial_por_placa, listar_usuarios, cambiar_estado_usuario  # noqa: E402
from app.contingency import validar_manual, actualizar_cache, sincronizar_cola  # noqa: E402
from app import zones  # noqa: E402
from app import reservations  # noqa: E402
from app import csrf  # noqa: E402
from app.email_service import EmailConfig, test_email_connection  # noqa: E402
from app import aceptacion  # noqa: E402
from app.scheduler import iniciar_scheduler, estado_scheduler  # noqa: E402

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "campus-parking-demo")
app.config["CSRF_OFF"] = os.getenv("CSRF_OFF", "0") == "1"

# Sprint 3 — M3-06: Iniciar scheduler de recordatorios
iniciar_scheduler()


@app.context_processor
def utilidades_contexto():
    def formatear_fecha(ts):
        if not ts:
            return "—"
        return str(ts).replace("T", " ")[:16]

    def csrf_input():
        return Markup(f'<input type="hidden" name="csrf_token" value="{csrf.generar_token()}"/>')

    return {"formatear_fecha": formatear_fecha, "csrf_input": csrf_input}

# Sprint 3 — M3-06: Iniciar scheduler de recordatorios
iniciar_scheduler()


@app.before_request
def _sincronizar_cola_contingencia():
    """Vuelca en la BD cualquier evento encolado por el modo contingencia (M1-04)."""
    sincronizar_cola()


@app.before_request
def _proteger_contra_csrf():
    """Exige un token CSRF válido en toda petición POST (C: seguridad básica)."""
    if request.method == "POST":
        csrf.validar_csrf()


@app.route("/")
def home():
    panel = zones.panel_cupos()
    total_ocupados = sum(z["ocupados"] for z in panel)
    return render_template("home.html", panel=panel, total_ocupados=total_ocupados)


# ---------------------------------------------------------------
# Sprint 1 — M1-01: registro y generación de QR
# ---------------------------------------------------------------
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        placa = request.form["placa"].strip().upper()
        rol = request.form["rol"]
        email = request.form.get("email", "").strip() or None
        conn = get_conn()
        ya_existia = conn.execute("SELECT 1 FROM usuarios WHERE placa = ?", (placa,)).fetchone()
        conn.close()
        try:
            generar_qr(nombre, placa, rol, email=email)
            actualizar_cache()  # mantiene el caché de contingencia al día (M1-04)
            flash("Placa ya registrada; QR regenerado." if ya_existia else f"QR generado para {placa}.", "success")
            return redirect(url_for("mi_qr", placa=placa))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash(f"No se pudo registrar: {e}", "danger")
    return render_template("registro.html")


@app.route("/mi-qr/<placa>")
def mi_qr(placa):
    return render_template("mi_qr.html", placa=placa.upper())


# ---------------------------------------------------------------
# Listado de todos los usuarios/vehículos registrados
# ---------------------------------------------------------------
@app.route("/usuarios")
def usuarios_registrados():
    return render_template("usuarios.html", usuarios=listar_usuarios())


@app.route("/qr-imagen/<placa>")
def qr_imagen(placa):
    ruta = os.path.join(DATA_DIR, "qrcodes", f"{placa.upper()}.png")
    if not os.path.exists(ruta):
        return "QR no encontrado", 404
    with open(ruta, "rb") as f:
        return Response(f.read(), mimetype="image/png")


# ---------------------------------------------------------------
# Sprint 1 — M1-02/M1-03: validador del vigilante (+ M2 zona / M3 reserva)
# ---------------------------------------------------------------
@app.route("/vigilante", methods=["GET", "POST"])
def vigilante():
    resultado = None
    zonas_disp = zones.listar_zonas()
    if request.method == "POST":
        placa = request.form.get("placa", "").strip().upper()
        zona = request.form.get("zona") or None
        ruta = os.path.join(DATA_DIR, "qrcodes", f"{placa}.png")
        if not placa_valida(placa) or not os.path.exists(ruta):
            flash(f"No existe un QR generado para la placa {placa}.", "danger")
        else:
            resultado = escanear(ruta, zona=zona)
    return render_template("vigilante.html", resultado=resultado, zonas=zonas_disp)


# ---------------------------------------------------------------
# Sprint 1 — M1-04: modo de contingencia
# ---------------------------------------------------------------
@app.route("/contingencia", methods=["GET", "POST"])
def contingencia():
    resultado = None
    if request.method == "POST":
        placa = request.form["placa"].strip().upper()
        ok = validar_manual(placa)
        resultado = {"valido": ok, "placa": placa}
    return render_template("contingencia.html", resultado=resultado)


# ---------------------------------------------------------------
# Sprint 2 — M2-01: administración de zonas
# ---------------------------------------------------------------
@app.route("/zonas", methods=["GET", "POST"])
def zonas_admin():
    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        aforo = int(request.form["aforo"])
        conn = get_conn()
        conn.execute("INSERT OR REPLACE INTO zonas (nombre, aforo_maximo) VALUES (?, ?)", (nombre, aforo))
        conn.commit()
        conn.close()
        flash(f"Zona '{nombre}' guardada con aforo {aforo}.", "success")
    return render_template("zonas.html", zonas=zones.listar_zonas())


# ---------------------------------------------------------------
# Sprint 2 — M2-02/M2-03/M2-06: panel de portería (auto-refresh)
# ---------------------------------------------------------------
@app.route("/panel")
def panel():
    return render_template("panel.html")


@app.route("/api/cupos")
def api_cupos():
    return jsonify(zones.panel_cupos())


# ---------------------------------------------------------------
# Sprint 2 — M2-04: consulta web/móvil para el conductor
# ---------------------------------------------------------------
@app.route("/disponibilidad")
def disponibilidad():
    return render_template("disponibilidad.html", panel=zones.panel_cupos())


# ---------------------------------------------------------------
# Sprint 2 — M2-05: métrica histórica de ocupación
# ---------------------------------------------------------------
@app.route("/metricas")
def metricas():
    return render_template("metricas.html", datos=zones.metrica_historica())


# ---------------------------------------------------------------
# Sprint 3 — M3-01/M3-02: reservas
# ---------------------------------------------------------------
@app.route("/reservar", methods=["GET", "POST"])
def reservar():
    if request.method == "POST":
        placa = request.form["placa"].strip().upper()
        zona = request.form["zona"]
        fecha = request.form["fecha"]
        hora_inicio = request.form["hora_inicio"]
        hora_fin = request.form["hora_fin"]
        try:
            reservations.crear_reserva(placa, zona, fecha, hora_inicio, hora_fin)
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("reservar.html", zonas=zones.listar_zonas())
        flash(f"Reserva creada para {placa} en {zona} ({hora_inicio}–{hora_fin}).", "success")
        return redirect(url_for("mis_reservas", placa=placa))
    return render_template("reservar.html", zonas=zones.listar_zonas())


@app.route("/mis-reservas/<placa>")
def mis_reservas(placa):
    liberadas = reservations.liberar_no_shows()
    conn = get_conn()
    filas = conn.execute(
        "SELECT * FROM reservas WHERE placa = ? ORDER BY fecha DESC, hora_inicio DESC", (placa.upper(),)
    ).fetchall()
    conn.close()
    return render_template("mis_reservas.html", placa=placa.upper(), reservas=[dict(f) for f in filas], liberadas=liberadas)


# ---------------------------------------------------------------
# Sprint 3 — M3-04: historial exportable
# ---------------------------------------------------------------
@app.route("/historial", methods=["GET", "POST"])
def historial():
    placa = request.values.get("placa") or None
    filas = historial_por_placa(placa) if placa else []
    return render_template("historial.html", placa=placa, filas=filas)


@app.route("/historial/csv")
def historial_csv_export():
    placa = request.args.get("placa") or None
    csv_data = reservations.historial_csv(placa=placa)
    return Response(
        csv_data, mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=historial.csv"},
    )


# ---------------------------------------------------------------
# Sprint 3 — M3-05: reporte de seguridad
# ---------------------------------------------------------------
@app.route("/reporte-seguridad")
def reporte_seguridad():
    fecha = request.args.get("fecha") or datetime.now().strftime("%Y-%m-%d")
    filas = reservations.reporte_sin_reserva(fecha)
    return render_template("reporte_seguridad.html", fecha=fecha, filas=filas)


# ---------------------------------------------------------------
# Cancelar reservas y dar de baja / reactivar vehículos
# ---------------------------------------------------------------
@app.route("/reservas/<int:reserva_id>/cancelar", methods=["POST"])
def cancelar_reserva(reserva_id):
    try:
        placa = reservations.cancelar_reserva(reserva_id)
        flash("Reserva cancelada. El cupo quedó libre.", "success")
        return redirect(url_for("mis_reservas", placa=placa))
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("reservar"))


@app.route("/vehiculos/<placa>/estado", methods=["POST"])
def estado_vehiculo(placa):
    activo = request.form.get("activo") == "1"
    try:
        cambiar_estado_usuario(placa, activo)
        actualizar_cache()  # el modo de contingencia debe ver el cambio
        flash(f"{placa.upper()} {'reactivado' if activo else 'dado de baja'}.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("usuarios_registrados"))


# ---------------------------------------------------------------
# Medición del tiempo de ingreso y aceptación del sponsor
# ---------------------------------------------------------------
@app.route("/medicion", methods=["GET", "POST"])
def medicion():
    if request.method == "POST":
        accion = request.form.get("accion", "registrar")
        try:
            if accion == "deshacer":
                flash("Se eliminó la última medición." if aceptacion.borrar_ultima_medicion()
                      else "No hay mediciones para eliminar.", "success")
            else:
                if request.form.get("minutos"):
                    segundos = float(request.form["minutos"].replace(",", ".")) * 60
                else:
                    segundos = request.form.get("segundos")
                aceptacion.registrar_medicion(segundos, request.form.get("placa"), request.form.get("fecha") or None)
                flash("Medición registrada.", "success")
        except ValueError as e:
            flash(str(e), "danger")
        return redirect(url_for("medicion"))
    return render_template("medicion.html", r=aceptacion.evaluar(), hoy=datetime.now().strftime("%Y-%m-%d"))


@app.route("/medicion/csv")
def medicion_csv():
    return Response(
        aceptacion.csv_mediciones(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=mediciones_ingreso.csv"},
    )


@app.route("/api/medicion")
def api_medicion():
    return jsonify(aceptacion.evaluar())


# ---------------------------------------------------------------
# Sprint 3 - M3-06: estado del scheduler y configuración de email
# ---------------------------------------------------------------
@app.route("/scheduler-status")
def scheduler_status():
    estado = estado_scheduler()
    return jsonify(estado)


@app.route("/sistema")
def sistema():
    email_cfg = {
        "host": EmailConfig.SMTP_HOST,
        "port": EmailConfig.SMTP_PORT,
        "from_email": EmailConfig.FROM_EMAIL,
        "from_name": EmailConfig.FROM_NAME,
        "configurado": EmailConfig.is_configured(),
    }
    return render_template("sistema.html", email_cfg=email_cfg, sched=estado_scheduler())


@app.route("/sistema/probar-email", methods=["POST"])
def sistema_probar_email():
    if not EmailConfig.is_configured():
        flash("El envío de correos no está configurado: define SMTP_USER y SMTP_PASSWORD en el archivo .env.", "warning")
    elif test_email_connection():
        flash("Conexión SMTP exitosa. Los recordatorios pueden enviarse.", "success")
    else:
        flash("Falló la conexión SMTP. Revisa host, puerto y credenciales en el archivo .env.", "danger")
    return redirect(url_for("sistema"))


if __name__ == "__main__":
    app.run(
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5050")),
    )
