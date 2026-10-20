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
except (UnicodeDecodeError, Exception) as e:  # Si hay problema de encoding, continuar sin .env
    print(f"[WARNING] No se pudo cargar .env file: {e}. Usando variables de entorno del sistema.")

from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify, session, abort
from markupsafe import Markup
from functools import wraps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import get_conn, DATA_DIR  # noqa: E402
from app.qr_generator import generar_qr, placa_valida  # noqa: E402
from app.validator import escanear, validar_token  # noqa: E402
from app.entry_log import historial_por_placa, listar_usuarios, cambiar_estado_usuario  # noqa: E402
from app.contingency import validar_manual, actualizar_cache, sincronizar_cola  # noqa: E402
from app import zones  # noqa: E402
from app import reservations  # noqa: E402
from app import csrf  # noqa: E402
from app import auth  # noqa: E402
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

    return {"formatear_fecha": formatear_fecha, "csrf_input": csrf_input,
            "correo_activo": EmailConfig.is_configured()}

# Sprint 3 — M3-06: Iniciar scheduler de recordatorios
iniciar_scheduler()


def rol_requerido(*roles):
    """Protege una ruta: sin sesión manda al login; con un rol no permitido responde 403.

    Roles: 'conductor' (entra con su correo), 'porteria' y 'admin' (entran con su usuario).
    """
    def decorador(f):
        @wraps(f)
        def envoltura(*args, **kwargs):
            rol = session.get("rol")
            if rol is None:
                flash("Debes iniciar sesión para acceder a esta página.", "warning")
                return redirect(url_for("login", next=request.full_path.rstrip("?")))
            if rol not in roles:
                abort(403)
            return f(*args, **kwargs)
        return envoltura
    return decorador


login_required = rol_requerido("conductor")
solo_porteria = rol_requerido("porteria", "admin")
solo_admin = rol_requerido("admin")


def _es_dueno(placa: str) -> bool:
    return session.get("rol") == "conductor" and session.get("user_placa") == (placa or "").upper()


def _siguiente_seguro(defecto: str) -> str:
    """Evita redirecciones a otros sitios: solo rutas internas como '/reservar'."""
    destino = request.args.get("next") or ""
    if destino.startswith("/") and not destino.startswith("//") and "\\" not in destino:
        return destino
    return defecto


def _iniciar_sesion(rol: str, nombre: str, placa: str = None, email: str = None) -> None:
    session.clear()  # sesión nueva en cada ingreso
    session["rol"] = rol
    session["user_name"] = nombre
    if placa:
        session["user_placa"] = placa
    if email:
        session["user_email"] = email


@app.before_request
def _sincronizar_cola_contingencia():
    """Vuelca en la BD cualquier evento encolado por el modo contingencia (M1-04)."""
    sincronizar_cola()


@app.before_request
def _proteger_contra_csrf():
    """Exige un token CSRF válido en toda petición POST (C: seguridad básica)."""
    if request.method == "POST":
        csrf.validar_csrf()


ERRORES = {
    400: ("Solicitud no válida", "El formulario venció o llegó incompleto. Recarga la página e inténtalo de nuevo."),
    403: ("Acceso denegado", "Tu cuenta no tiene permiso para ver esta página."),
    404: ("Página no encontrada", "La dirección que escribiste no existe."),
    500: ("Error interno", "Algo falló de nuestro lado. Inténtalo de nuevo en un momento."),
}


@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(500)
def pagina_de_error(error):
    codigo = getattr(error, "code", 500) or 500
    titulo, mensaje = ERRORES.get(codigo, ERRORES[500])
    return render_template("403.html", titulo=titulo, mensaje=mensaje), codigo


def _inicio_del_rol():
    """Pantalla de llegada de cada rol."""
    return {"conductor": url_for("dashboard"), "porteria": url_for("vigilante"),
            "admin": url_for("resumen_admin")}.get(session.get("rol"), url_for("home"))


@app.route("/")
def home():
    """Portada pública. Con sesión iniciada, cada rol va directo a su pantalla."""
    if session.get("rol"):
        return redirect(_inicio_del_rol())
    return render_template("home.html", panel=zones.panel_cupos())


# ---------------------------------------------------------------
# Inicio de sesión único: correo (conductores) o usuario del personal
# ---------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("rol"):
        return redirect(_inicio_del_rol())
    if request.method == "POST":
        usuario = (request.form.get("usuario") or request.form.get("email") or "").strip().lower()
        clave = request.form.get("password", "")

        if not usuario or not clave:
            flash("Ingresa tu correo o usuario y tu contraseña.", "danger")
            return render_template("login.html", usuario=usuario)

        if usuario in auth.CUENTAS_PERSONAL:
            if auth.verificar_personal(usuario, clave):
                _iniciar_sesion(usuario, "Administrador" if usuario == "admin" else "Vigilante")
                return redirect(_siguiente_seguro(_inicio_del_rol()))
        else:
            conductor = auth.verificar_conductor(usuario, clave)
            if conductor:
                _iniciar_sesion("conductor", conductor["nombre"], placa=conductor["placa"], email=conductor["email"])
                flash(f"¡Bienvenido/a, {conductor['nombre']}!", "success")
                return redirect(_siguiente_seguro(url_for("dashboard")))
            if auth.tiene_cuenta_sin_clave(usuario):
                flash("Tu registro es anterior a las contraseñas: vuelve a registrar tu vehículo con la "
                      "misma placa y el mismo correo para crear tu contraseña.", "warning")
                return redirect(url_for("registro"))
        # Mismo mensaje en todos los casos: no revela qué cuentas existen
        flash("Usuario o contraseña incorrectos.", "danger")
        return render_template("login.html", usuario=usuario)

    return render_template("login.html")


@app.route("/personal")
def login_personal():
    """Dirección antigua del ingreso de personal: ahora todos entran por /login."""
    return redirect(url_for("login", next=request.args.get("next")))


@app.route("/logout")
def logout():
    nombre = session.get('user_name', 'Usuario')
    session.clear()
    flash(f"¡Hasta pronto, {nombre}!", "info")
    return redirect(url_for('home'))


@app.route("/dashboard")
@login_required
def dashboard():
    """Dashboard del usuario después de iniciar sesión."""
    placa = session.get('user_placa')

    # Obtener reservas del usuario
    liberadas = reservations.liberar_no_shows()
    conn = get_conn()
    reservas = conn.execute(
        "SELECT * FROM reservas WHERE placa = ? ORDER BY fecha DESC, hora_inicio DESC LIMIT 5",
        (placa,)
    ).fetchall()

    # Obtener información del usuario
    usuario = conn.execute("SELECT * FROM usuarios WHERE placa = ?", (placa,)).fetchone()
    conn.close()

    return render_template(
        "dashboard.html",
        usuario=dict(usuario),
        reservas=[dict(r) for r in reservas],
        panel=zones.panel_cupos()
    )


# ---------------------------------------------------------------
# Sprint 1 — M1-01: registro y generación de QR
# ---------------------------------------------------------------
@app.route("/registro", methods=["GET", "POST"])
def registro():
    rol_actual = session.get("rol")
    if rol_actual == "conductor":
        flash("Ya tienes sesión iniciada. Para registrar otro vehículo, cierra sesión primero.", "info")
        return redirect(url_for("dashboard"))
    if rol_actual == "porteria":
        abort(403)
    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        placa = request.form["placa"].strip().upper()
        rol = request.form["rol"]
        email = request.form.get("email", "").strip()
        clave = request.form.get("password", "")
        try:
            if not placa_valida(placa):
                raise ValueError("La placa debe tener entre 5 y 7 letras o números (ej. ABC123), sin espacios ni símbolos.")
            if not email:
                raise ValueError("El correo es obligatorio: con él inicias sesión.")
            auth.validar_clave_nueva(clave, request.form.get("password2", ""))
            existente = auth.datos_placa(placa)
            if existente is not None:
                # Nadie puede reescribir los datos de una placa ajena. Solo un registro antiguo
                # (sin contraseña) puede crearla, y únicamente con el mismo correo.
                if existente["password_hash"] or (existente["email"] or "").lower() != email.lower():
                    raise ValueError(f"La placa {placa} ya está registrada. Si es tuya, inicia sesión.")
            generar_qr(nombre, placa, rol, email=email)
            auth.guardar_clave(placa, clave)
            actualizar_cache()  # mantiene el caché de contingencia al día (M1-04)
            if rol_actual != "admin":  # el admin registra a nombre de otro y conserva su sesión
                _iniciar_sesion("conductor", nombre, placa=placa, email=email)
            flash("Contraseña creada; QR regenerado." if existente else f"QR generado para {placa}.", "success")
            return redirect(url_for("mi_qr", placa=placa))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash(f"No se pudo registrar: {e}", "danger")
    return render_template("registro.html")


@app.route("/mi-qr/<placa>")
@rol_requerido("conductor", "admin")
def mi_qr(placa):
    if session["rol"] != "admin" and not _es_dueno(placa):
        abort(403)
    return render_template("mi_qr.html", placa=placa.upper())


# ---------------------------------------------------------------
# Resumen del administrador: lo más importante del día en una pantalla
# ---------------------------------------------------------------
@app.route("/resumen")
@solo_admin
def resumen_admin():
    hoy = datetime.now().strftime("%Y-%m-%d")
    panel = zones.panel_cupos()
    conn = get_conn()
    reservas_hoy = conn.execute(
        "SELECT COUNT(*) FROM reservas WHERE fecha = ? AND estado IN ('activa','usada')", (hoy,)
    ).fetchone()[0]
    movimientos = conn.execute(
        """SELECT r.placa, r.tipo, r.metodo, r.zona, r.timestamp, u.nombre
           FROM registros r LEFT JOIN usuarios u ON u.placa = r.placa
           ORDER BY r.id DESC LIMIT 8"""
    ).fetchall()
    conn.close()
    return render_template(
        "resumen.html",
        panel=panel,
        dentro=sum(z["ocupados"] for z in panel),
        libres=sum(z["disponibles"] for z in panel),
        reservas_hoy=reservas_hoy,
        sin_reserva=len(reservations.reporte_sin_reserva(hoy)),
        zonas_llenas=[z["zona"] for z in panel if z["alerta_llena"]],
        movimientos=[dict(m) for m in movimientos],
    )


# ---------------------------------------------------------------
# Listado de todos los usuarios/vehículos registrados
# ---------------------------------------------------------------
@app.route("/usuarios")
@solo_admin
def usuarios_registrados():
    return render_template("usuarios.html", usuarios=listar_usuarios())


@app.route("/qr-imagen/<placa>")
@rol_requerido("conductor", "admin")
def qr_imagen(placa):
    if session["rol"] != "admin" and not _es_dueno(placa):
        abort(403)
    ruta =os.path.join(DATA_DIR, "qrcodes", f"{placa.upper()}.png")
    if not os.path.exists(ruta):
        return "QR no encontrado", 404
    with open(ruta, "rb") as f:
        return Response(f.read(), mimetype="image/png")


# ---------------------------------------------------------------
# Sprint 1 — M1-02/M1-03: validador del vigilante (+ M2 zona / M3 reserva)
# ---------------------------------------------------------------
@app.route("/vigilante", methods=["GET", "POST"])
@solo_porteria
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
@solo_porteria
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
@solo_admin
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
@solo_porteria
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
@solo_admin
def metricas():
    return render_template("metricas.html", datos=zones.metrica_historica())


# ---------------------------------------------------------------
# Sprint 3 — M3-01/M3-02: reservas
# ---------------------------------------------------------------
@app.route("/reservar", methods=["GET", "POST"])
@login_required
def reservar():
    if request.method == "POST":
        # Usar la placa del usuario logueado
        placa = session.get('user_placa')
        zona = request.form["zona"]
        fecha = request.form["fecha"]
        hora_inicio = request.form["hora_inicio"]
        hora_fin = request.form["hora_fin"]
        try:
            reservations.crear_reserva(placa, zona, fecha, hora_inicio, hora_fin, enviar_confirmacion=True)
            flash("¡Reserva creada! Revisa tu correo para ver la confirmación." if EmailConfig.is_configured()
                  else "¡Reserva creada!", "success")
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("reservar.html", zonas=zones.listar_zonas(), placa=placa)
        return redirect(url_for("dashboard"))

    placa = session.get('user_placa')
    return render_template("reservar.html", zonas=zones.listar_zonas(), placa=placa)


@app.route("/mis-reservas/<placa>")
@rol_requerido("conductor", "admin")
def mis_reservas(placa):
    if session["rol"] != "admin" and not _es_dueno(placa):
        abort(403)
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
@solo_admin
def historial():
    placa = request.values.get("placa") or None
    filas = historial_por_placa(placa) if placa else []
    return render_template("historial.html", placa=placa, filas=filas)


@app.route("/historial/csv")
@solo_admin
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
@solo_porteria
def reporte_seguridad():
    fecha = request.args.get("fecha") or datetime.now().strftime("%Y-%m-%d")
    filas = reservations.reporte_sin_reserva(fecha)
    return render_template("reporte_seguridad.html", fecha=fecha, filas=filas)


# ---------------------------------------------------------------
# Cancelar reservas y dar de baja / reactivar vehículos
# ---------------------------------------------------------------
@app.route("/reservas/<int:reserva_id>/cancelar", methods=["POST"])
@rol_requerido("conductor", "admin")
def cancelar_reserva(reserva_id):
    conn = get_conn()
    fila = conn.execute("SELECT placa FROM reservas WHERE id = ?", (reserva_id,)).fetchone()
    conn.close()
    if fila and session["rol"] != "admin" and not _es_dueno(fila["placa"]):
        abort(403)
    try:
        placa = reservations.cancelar_reserva(reserva_id)
        flash("Reserva cancelada. El cupo quedó libre.", "success")
        return redirect(url_for("mis_reservas", placa=placa))
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("reservar") if session["rol"] == "conductor" else url_for("usuarios_registrados"))


@app.route("/vehiculos/<placa>/estado", methods=["POST"])
@solo_admin
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
@solo_admin
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
@solo_admin
def medicion_csv():
    return Response(
        aceptacion.csv_mediciones(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=mediciones_ingreso.csv"},
    )


@app.route("/api/medicion")
@solo_admin
def api_medicion():
    return jsonify(aceptacion.evaluar())


# ---------------------------------------------------------------
# Sprint 3 - M3-06: estado del scheduler y configuración de email
# ---------------------------------------------------------------
@app.route("/scheduler-status")
@solo_admin
def scheduler_status():
    estado = estado_scheduler()
    return jsonify(estado)


@app.route("/sistema")
@solo_admin
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
@solo_admin
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
        load_dotenv=False,  # Ya cargamos dotenv arriba con manejo de errores
    )
