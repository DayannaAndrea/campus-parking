"""
Medición de aceptación: el sponsor firma solo si el tiempo promedio de ingreso
es de 3 minutos o menos durante 5 días hábiles consecutivos, con al menos 20
vehículos medidos cada día.
"""
import statistics
from datetime import date, datetime, timedelta

from app.db import get_conn

META_MIN = 3.0
DIAS_REQUERIDOS = 5
MIN_VEHICULOS = 20
MAX_SEGUNDOS = 3600


def registrar_medicion(segundos: float, placa: str = None, fecha: str = None) -> None:
    """Guarda el tiempo (en segundos) que tardó un vehículo en ingresar."""
    try:
        segundos = float(segundos)
    except (TypeError, ValueError):
        raise ValueError("El tiempo debe ser un número de segundos.")
    if not (0 < segundos <= MAX_SEGUNDOS):
        raise ValueError("El tiempo debe estar entre 1 segundo y 60 minutos.")
    fecha = fecha or datetime.now().strftime("%Y-%m-%d")
    try:
        date.fromisoformat(fecha)
    except ValueError:
        raise ValueError("La fecha debe tener el formato AAAA-MM-DD.")
    placa = (placa or "").strip().upper() or None
    conn = get_conn()
    conn.execute(
        "INSERT INTO mediciones (fecha, placa, segundos, creada) VALUES (?, ?, ?, ?)",
        (fecha, placa, segundos, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()


def borrar_ultima_medicion() -> bool:
    """Deshace el último registro (por si el vigilante se equivoca al cronometrar)."""
    conn = get_conn()
    fila = conn.execute("SELECT id FROM mediciones ORDER BY id DESC LIMIT 1").fetchone()
    if fila:
        conn.execute("DELETE FROM mediciones WHERE id = ?", (fila["id"],))
        conn.commit()
    conn.close()
    return bool(fila)


def _siguiente_habil(d: date) -> date:
    d += timedelta(days=1)
    while d.weekday() >= 5:  # sábado y domingo no cuentan
        d += timedelta(days=1)
    return d


def evaluar() -> dict:
    """Resumen por día, racha vigente de días que cumplen y dictamen final."""
    conn = get_conn()
    filas = conn.execute("SELECT fecha, segundos FROM mediciones ORDER BY fecha").fetchall()
    conn.close()

    por_dia = {}
    for f in filas:
        por_dia.setdefault(f["fecha"], []).append(f["segundos"])

    dias = []
    for fecha in sorted(por_dia):
        t = por_dia[fecha]
        prom_min = statistics.mean(t) / 60
        if len(t) < MIN_VEHICULOS:
            motivo = f"faltan {MIN_VEHICULOS - len(t)} vehículos"
        elif prom_min > META_MIN:
            motivo = "supera la meta"
        else:
            motivo = "cumple"
        dias.append({
            "fecha": fecha,
            "vehiculos": len(t),
            "promedio_min": round(prom_min, 2),
            "cumple": motivo == "cumple",
            "motivo": motivo,
        })

    mejor = racha = 0
    previo = None
    for d in dias:
        actual = date.fromisoformat(d["fecha"])
        if d["cumple"]:
            continuo = previo is not None and actual == _siguiente_habil(previo)
            racha = racha + 1 if continuo else 1
            previo = actual
        else:
            racha = 0
            previo = None
        mejor = max(mejor, racha)

    total = sum(len(v) for v in por_dia.values())
    promedio_global = round(statistics.mean(s for v in por_dia.values() for s in v) / 60, 2) if total else None
    aprobado = mejor >= DIAS_REQUERIDOS
    return {
        "dias": dias,
        "racha": racha,
        "mejor_racha": mejor,
        "requeridos": DIAS_REQUERIDOS,
        "meta_min": META_MIN,
        "min_vehiculos": MIN_VEHICULOS,
        "total_mediciones": total,
        "promedio_global_min": promedio_global,
        "aprobado": aprobado,
    }


def csv_mediciones() -> str:
    import csv
    import io

    conn = get_conn()
    filas = conn.execute("SELECT fecha, placa, segundos, creada FROM mediciones ORDER BY id").fetchall()
    conn.close()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["fecha", "placa", "segundos", "registrada"])
    for f in filas:
        w.writerow([f["fecha"], f["placa"] or "", f["segundos"], f["creada"]])
    return buf.getvalue()
