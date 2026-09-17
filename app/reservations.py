"""
Historias del Sprint 3:

M3-01 — Reserva por franja horaria.
M3-02 — Liberación automática por no-show (15 min de tolerancia).
M3-03 — Validar si una placa tiene reserva vigente al escanear el QR.
M3-04 — Historial exportable (CSV).
M3-05 — Reporte de placas sin reserva que ingresaron.
"""
import csv
import io
from datetime import datetime, timedelta

from app.db import get_conn

TOLERANCIA_NOSHOW_MIN = 15


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
