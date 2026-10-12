"""
Aceptación del sponsor — promedio de ingreso <= 3 min durante 5 días reales consecutivos.

Uso:
  python3 tests/medicion_5_dias.py agregar 2026-10-12 2.8 3.1 2.5 ...   # minutos de cada vehículo del día
  python3 tests/medicion_5_dias.py evaluar                               # dictamen final

Los datos quedan en tests/mediciones_aceptacion.csv (fecha,minutos).
Se necesitan al menos 20 vehículos por día (igual que el checklist de portería).
"""
import csv
import os
import statistics
import sys
from datetime import date, timedelta

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mediciones_aceptacion.csv")
META_MIN = 3.0
DIAS_REQUERIDOS = 5
MIN_VEHICULOS = 20


def _leer():
    por_dia = {}
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, newline="") as fh:
            for fila in csv.DictReader(fh):
                por_dia.setdefault(fila["fecha"], []).append(float(fila["minutos"]))
    return por_dia


def agregar(fecha, tiempos):
    nuevo = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as fh:
        w = csv.writer(fh)
        if nuevo:
            w.writerow(["fecha", "minutos"])
        for t in tiempos:
            w.writerow([fecha, t])
    print(f"{len(tiempos)} mediciones guardadas para {fecha}.")


def _consecutivos(fechas):
    """Cuenta la racha más larga de días hábiles consecutivos (lun-vie, saltando fin de semana)."""
    ds = sorted(date.fromisoformat(f) for f in fechas)
    mejor = racha = 1 if ds else 0
    for a, b in zip(ds, ds[1:]):
        sig = a + timedelta(days=1)
        while sig.weekday() >= 5:
            sig += timedelta(days=1)
        racha = racha + 1 if b == sig else 1
        mejor = max(mejor, racha)
    return mejor


def evaluar():
    por_dia = _leer()
    if not por_dia:
        print("Aún no hay mediciones.")
        return False
    print(f"{'Día':<12}{'Vehículos':>10}{'Promedio (min)':>16}  Estado")
    cumple_todos = True
    for f in sorted(por_dia):
        t = por_dia[f]
        prom = statistics.mean(t)
        ok = prom <= META_MIN and len(t) >= MIN_VEHICULOS
        cumple_todos &= ok
        motivo = "OK" if ok else ("pocos vehículos" if len(t) < MIN_VEHICULOS else "supera la meta")
        print(f"{f:<12}{len(t):>10}{prom:>16.2f}  {motivo}")
    racha = _consecutivos(por_dia)
    print(f"\nDías consecutivos medidos: {racha} de {DIAS_REQUERIDOS} requeridos")
    aprobado = cumple_todos and racha >= DIAS_REQUERIDOS
    print("DICTAMEN:", "CUMPLE — el sponsor puede firmar la aceptación." if aprobado else "AÚN NO CUMPLE.")
    return aprobado


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "agregar":
        agregar(sys.argv[2], [float(x) for x in sys.argv[3:]])
    elif len(sys.argv) == 2 and sys.argv[1] == "evaluar":
        evaluar()
    else:
        print(__doc__)
