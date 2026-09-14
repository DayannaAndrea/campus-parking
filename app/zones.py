"""
Historias del Sprint 2:

M2-01 — Modelar zonas y aforo máximo.
M2-02 — Contador de ocupación en tiempo real por zona.
M2-05 — Métrica histórica de ocupación por zona.
M2-06 — Alerta cuando una zona llega al 100%.
"""
from app.db import get_conn


def listar_zonas():
    conn = get_conn()
    filas = conn.execute("SELECT * FROM zonas ORDER BY nombre").fetchall()
    conn.close()
    return [dict(f) for f in filas]


def ocupacion_actual(zona_nombre: str) -> int:
    """Vehículos actualmente dentro de una zona: cuenta placas cuyo último
    registro en esa zona es 'entrada' (sin salida posterior)."""
    conn = get_conn()
    filas = conn.execute(
        """
        SELECT placa, tipo FROM registros r
        WHERE zona = ?
          AND id = (SELECT MAX(id) FROM registros r2 WHERE r2.placa = r.placa AND r2.zona = ?)
        """,
        (zona_nombre, zona_nombre),
    ).fetchall()
    conn.close()
    return sum(1 for f in filas if f["tipo"] == "entrada")


def panel_cupos():
    """M2-02 + M2-06: ocupación, disponibles y alerta por zona."""
    panel = []
    for z in listar_zonas():
        ocupados = ocupacion_actual(z["nombre"])
        disponibles = max(z["aforo_maximo"] - ocupados, 0)
        panel.append({
            "zona": z["nombre"],
            "aforo_maximo": z["aforo_maximo"],
            "ocupados": ocupados,
            "disponibles": disponibles,
            "porcentaje": round(100 * ocupados / z["aforo_maximo"]) if z["aforo_maximo"] else 0,
            "alerta_llena": disponibles == 0,
        })
    return panel


def metrica_historica(zona_nombre: str = None):
    """M2-05: % de ocupación promedio por zona (a partir del histórico de entradas)."""
    conn = get_conn()
    if zona_nombre:
        filas = conn.execute(
            "SELECT zona, COUNT(*) AS entradas FROM registros WHERE tipo='entrada' AND zona = ? GROUP BY zona",
            (zona_nombre,),
        ).fetchall()
    else:
        filas = conn.execute(
            "SELECT zona, COUNT(*) AS entradas FROM registros WHERE tipo='entrada' AND zona IS NOT NULL GROUP BY zona"
        ).fetchall()
    conn.close()
    return [dict(f) for f in filas]
