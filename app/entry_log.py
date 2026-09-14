"""
Historia M1-03 — Registro automático de entrada/salida al escanear.

Criterio de aceptación:
- Cada escaneo válido crea un registro con marca de tiempo.
- El tipo (entrada/salida) se determina automáticamente alternando según
  el último registro de esa placa.
- Es consultable por placa.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db import get_conn, ultimo_tipo_registro  # noqa: E402


def registrar_evento(placa: str, metodo: str = "qr", zona: str = None) -> str:
    ultimo = ultimo_tipo_registro(placa)
    tipo = "salida" if ultimo == "entrada" else "entrada"

    conn = get_conn()
    conn.execute(
        "INSERT INTO registros (placa, tipo, metodo, zona, timestamp) VALUES (?, ?, ?, ?, ?)",
        (placa, tipo, metodo, zona, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()
    return tipo


def historial_por_placa(placa: str):
    conn = get_conn()
    filas = conn.execute(
        "SELECT tipo, metodo, timestamp FROM registros WHERE placa = ? ORDER BY id",
        (placa,),
    ).fetchall()
    conn.close()
    return [dict(f) for f in filas]


def listar_usuarios():
    """Todos los vehículos/usuarios registrados, con su último movimiento
    (para saber si están 'Dentro' o 'Fuera' del campus en este momento)."""
    conn = get_conn()
    usuarios = conn.execute(
        "SELECT nombre, placa, rol, activo FROM usuarios ORDER BY id DESC"
    ).fetchall()
    resultado = []
    for u in usuarios:
        u = dict(u)
        ultimo = conn.execute(
            "SELECT tipo, timestamp FROM registros WHERE placa = ? ORDER BY id DESC LIMIT 1",
            (u["placa"],),
        ).fetchone()
        u["estado"] = "Dentro" if (ultimo and ultimo["tipo"] == "entrada") else "Fuera"
        u["ultimo_movimiento"] = ultimo["timestamp"] if ultimo else None
        resultado.append(u)
    conn.close()
    return resultado


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Uso: python3 app/entry_log.py <PLACA>")
        raise SystemExit(1)
    for r in historial_por_placa(sys.argv[1].upper()):
        print(r)
