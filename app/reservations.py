"""
Historias del Sprint 3:

M3-01 — Reserva por franja horaria.
M3-02 — Liberación automática por no-show (15 min de tolerancia).
M3-03 — Validar si una placa tiene reserva vigente al escanear el QR.
M3-04 — Historial exportable (CSV).
M3-05 — Reporte de placas sin reserva que ingresaron.
M3-06 — Recordatorio por correo institucional 15 min antes del inicio.
"""
import csv
import io
from datetime import datetime, timedelta

from app.db import get_conn
from app.email_service import enviar_email

TOLERANCIA_NOSHOW_MIN = 15
VENTANA_RECORDATORIO_MIN = 15


def crear_reserva(placa: str, zona: str, fecha: str, hora_inicio: str, hora_fin: str):
    placa = placa.strip().upper()
    try:
        hora_ini = datetime.strptime(hora_inicio, "%H:%M").time()
        hora_fin_dt = datetime.strptime(hora_fin, "%H:%M").time()
        datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Formato inválido: fecha YYYY-MM-DD y horas HH:MM.")
    if hora_ini >= hora_fin_dt:
        raise ValueError("La hora de fin debe ser mayor que la de inicio.")

    conn = get_conn()
    if not conn.execute("SELECT 1 FROM usuarios WHERE placa = ?", (placa,)).fetchone():
        conn.close()
        raise ValueError(f"La placa {placa} no está registrada. Regístrala antes de reservar.")

    aforo = conn.execute("SELECT aforo_maximo FROM zonas WHERE nombre = ?", (zona,)).fetchone()
    if not aforo:
        conn.close()
        raise ValueError(f"La zona '{zona}' no existe.")

    reservadas = conn.execute(
        """SELECT COUNT(*) AS n FROM reservas
           WHERE zona = ? AND fecha = ? AND estado IN ('activa','usada')
             AND ? < hora_fin AND hora_inicio < ?""",
        (zona, fecha, hora_inicio, hora_fin),
    ).fetchone()["n"]
    if reservadas >= aforo["aforo_maximo"]:
        conn.close()
        raise ValueError(f"La zona {zona} ya está llena en esa franja horaria.")

    duplicada = conn.execute(
        """SELECT 1 FROM reservas WHERE placa = ? AND fecha = ? AND estado IN ('activa','usada')
           AND ? < hora_fin AND hora_inicio < ? LIMIT 1""",
        (placa, fecha, hora_inicio, hora_fin),
    ).fetchone()
    if duplicada:
        conn.close()
        raise ValueError("Ya tienes una reserva activa en esa franja horaria.")

    conn.execute(
        """INSERT INTO reservas (placa, zona, fecha, hora_inicio, hora_fin, estado, creada)
           VALUES (?, ?, ?, ?, ?, 'activa', ?)""",
        (placa, zona, fecha, hora_inicio, hora_fin, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()


def liberar_no_shows():
    """M3-02: libera automáticamente reservas activas cuyo inicio + tolerancia ya pasó
    y la placa nunca registró entrada dentro de esa franja."""
    conn = get_conn()
    activas = conn.execute("SELECT * FROM reservas WHERE estado = 'activa'").fetchall()
    ahora = datetime.now()
    liberadas = 0
    for r in activas:
        inicio = datetime.fromisoformat(f"{r['fecha']}T{r['hora_inicio']}")
        limite = inicio + timedelta(minutes=TOLERANCIA_NOSHOW_MIN)
        if ahora > limite:
            entro = conn.execute(
                """SELECT 1 FROM registros WHERE placa = ? AND tipo = 'entrada'
                   AND timestamp BETWEEN ? AND ? LIMIT 1""",
                (r["placa"], inicio.isoformat(timespec="seconds"), limite.isoformat(timespec="seconds")),
            ).fetchone()
            if not entro:
                conn.execute("UPDATE reservas SET estado = 'liberada' WHERE id = ?", (r["id"],))
                liberadas += 1
    conn.commit()
    conn.close()
    return liberadas


def reserva_vigente(placa: str):
    """M3-03: usada por el validador del vigilante al escanear el QR."""
    liberar_no_shows()
    conn = get_conn()
    hoy = datetime.now().strftime("%Y-%m-%d")
    ahora_hhmm = datetime.now().strftime("%H:%M")
    fila = conn.execute(
        """SELECT * FROM reservas WHERE placa = ? AND fecha = ? AND estado = 'activa'
           AND ? BETWEEN hora_inicio AND hora_fin""",
        (placa.upper(), hoy, ahora_hhmm),
    ).fetchone()
    conn.close()
    return dict(fila) if fila else None


def marcar_reserva_usada(placa: str, reserva_id: int = None):
    conn = get_conn()
    if reserva_id is not None:
        conn.execute("UPDATE reservas SET estado='usada' WHERE id = ?", (reserva_id,))
    else:
        conn.execute(
            "UPDATE reservas SET estado='usada' WHERE placa = ? AND estado = 'activa'",
            (placa.upper(),),
        )
    conn.commit()
    conn.close()


def historial_csv(placa: str = None, desde: str = None, hasta: str = None) -> str:
    """M3-04: exporta el historial de entradas/salidas filtrado."""
    conn = get_conn()
    query = "SELECT placa, tipo, metodo, zona, timestamp FROM registros WHERE 1=1"
    params = []
    if placa:
        query += " AND placa = ?"
        params.append(placa.upper())
    if desde:
        query += " AND timestamp >= ?"
        params.append(desde)
    if hasta:
        query += " AND timestamp <= ?"
        params.append(hasta)
    query += " ORDER BY timestamp"
    filas = conn.execute(query, params).fetchall()
    conn.close()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["placa", "tipo", "metodo", "zona", "timestamp"])
    for f in filas:
        writer.writerow([f["placa"], f["tipo"], f["metodo"], f["zona"], f["timestamp"]])
    return buf.getvalue()


def reporte_sin_reserva(fecha: str = None):
    """M3-05: placas que ingresaron ese día sin una reserva vigente en ese momento."""
    fecha = fecha or datetime.now().strftime("%Y-%m-%d")
    conn = get_conn()
    entradas = conn.execute(
        "SELECT placa, zona, timestamp, metodo FROM registros WHERE tipo='entrada' AND timestamp LIKE ?",
        (f"{fecha}%",),
    ).fetchall()
    resultado = []
    for e in entradas:
        hhmm = e["timestamp"].split("T")[1][:5]
        tiene_reserva = conn.execute(
            """SELECT 1 FROM reservas WHERE placa = ? AND fecha = ?
               AND ? BETWEEN hora_inicio AND hora_fin AND estado IN ('activa','usada')""",
            (e["placa"], fecha, hhmm),
        ).fetchone()
        if not tiene_reserva:
            resultado.append(dict(e))
    conn.close()
    return resultado


def obtener_reservas_proximas():
    """
    M3-06: Obtiene reservas que necesitan recordatorio.

    Busca reservas activas cuyo inicio esté dentro de los próximos 15 minutos
    y que aún no hayan recibido recordatorio.

    Returns:
        Lista de diccionarios con datos de reserva y usuario
    """
    conn = get_conn()
    ahora = datetime.now()
    ventana_inicio = ahora + timedelta(minutes=VENTANA_RECORDATORIO_MIN - 2)
    ventana_fin = ahora + timedelta(minutes=VENTANA_RECORDATORIO_MIN + 2)

    # Buscar reservas en la ventana de tiempo que no tengan recordatorio enviado
    reservas = conn.execute(
        """
        SELECT r.*, u.nombre, u.rol
        FROM reservas r
        JOIN usuarios u ON r.placa = u.placa
        WHERE r.estado = 'activa'
          AND r.recordatorio_enviado = 0
          AND datetime(r.fecha || 'T' || r.hora_inicio) BETWEEN ? AND ?
        """,
        (ventana_inicio.isoformat(timespec="seconds"), ventana_fin.isoformat(timespec="seconds")),
    ).fetchall()
    conn.close()

    return [dict(r) for r in reservas]


def enviar_recordatorio_reserva(reserva_id: int) -> bool:
    """
    M3-06: Envía recordatorio por email para una reserva específica.

    Args:
        reserva_id: ID de la reserva

    Returns:
        True si el email se envió correctamente
    """
    conn = get_conn()
    reserva = conn.execute(
        """
        SELECT r.*, u.nombre, u.rol
        FROM reservas r
        JOIN usuarios u ON r.placa = u.placa
        WHERE r.id = ?
        """,
        (reserva_id,),
    ).fetchone()

    if not reserva:
        conn.close()
        return False

    # Construir email institucional (simulado)
    email_usuario = f"{reserva['placa'].lower().replace('-', '')}@campus.edu"

    asunto = "🅿️ Recordatorio: Tu reserva de parqueadero inicia en 15 minutos"

    cuerpo_texto = f"""
Hola {reserva['nombre']},

Este es un recordatorio de tu reserva de parqueadero:

📍 Zona: {reserva['zona']}
📅 Fecha: {reserva['fecha']}
⏰ Horario: {reserva['hora_inicio']} - {reserva['hora_fin']}
🚗 Placa: {reserva['placa']}

Tu reserva comienza en aproximadamente 15 minutos.

⚠️ IMPORTANTE: Si no ingresas dentro de los primeros 15 minutos de tu franja horaria,
la reserva se liberará automáticamente para otros usuarios.

¡Nos vemos pronto!

Campus Parking
Sistema de Control de Entradas y Cupos
"""

    # Enviar email
    enviado = enviar_email(email_usuario, asunto, cuerpo_texto)

    # Marcar como enviado en la BD
    if enviado:
        conn.execute(
            "UPDATE reservas SET recordatorio_enviado = 1 WHERE id = ?",
            (reserva_id,),
        )
        conn.commit()

    conn.close()
    return enviado


def procesar_recordatorios() -> int:
    """
    M3-06: Procesa y envía todos los recordatorios pendientes.

    Returns:
        Número de recordatorios enviados exitosamente
    """
    reservas_proximas = obtener_reservas_proximas()
    enviados = 0

    for reserva in reservas_proximas:
        if enviar_recordatorio_reserva(reserva["id"]):
            enviados += 1

    return enviados
