"""
Historia M1-04 — Modo de contingencia por placa si falla la red o el escáner.

Criterio de aceptación:
- Existe un modo manual donde el vigilante escribe la placa.
- El sistema valida contra una copia local/caché de placas autorizadas
  (funciona aunque no haya red).
- El registro se encola y se sincroniza cuando vuelve la red.
"""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db import get_conn, DATA_DIR, ultimo_tipo_registro  # noqa: E402

CACHE_PATH = os.path.join(DATA_DIR, "cache_placas.json")
COLA_PATH = os.path.join(DATA_DIR, "cola_sincronizacion.json")


def actualizar_cache():
    """Se ejecuta periódicamente (ej. cada hora) mientras hay red, para que
    el modo de contingencia siempre tenga una copia reciente."""
    conn = get_conn()
    filas = conn.execute("SELECT placa, nombre, activo FROM usuarios").fetchall()
    conn.close()
    cache = {f["placa"]: {"nombre": f["nombre"], "activo": f["activo"]} for f in filas}
    with open(CACHE_PATH, "w") as fh:
        json.dump(cache, fh, ensure_ascii=False, indent=2)
    return cache


def _leer_cache():
    if not os.path.exists(CACHE_PATH):
        return actualizar_cache()
    with open(CACHE_PATH) as fh:
        return json.load(fh)


def _encolar(placa: str, tipo: str):
    cola = []
    if os.path.exists(COLA_PATH):
        with open(COLA_PATH) as fh:
            cola = json.load(fh)
    cola.append(
        {
            "placa": placa,
            "tipo": tipo,
            "metodo": "contingencia",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )
    with open(COLA_PATH, "w") as fh:
        json.dump(cola, fh, ensure_ascii=False, indent=2)


def sincronizar_cola():
    """Se ejecuta al recuperar la red (y en cada request: vuelca la cola a la BD)."""
    if not os.path.exists(COLA_PATH):
        return 0
    with open(COLA_PATH) as fh:
        cola = json.load(fh)
    conn = get_conn()
    for evento in cola:
        zona = evento.get("zona")
        if evento["tipo"] == "salida" and not zona:
            fila = conn.execute(
                "SELECT zona FROM registros WHERE placa = ? AND tipo = 'entrada' ORDER BY id DESC LIMIT 1",
                (evento["placa"],),
            ).fetchone()
            zona = fila["zona"] if fila else None
        conn.execute(
            "INSERT INTO registros (placa, tipo, metodo, zona, timestamp) VALUES (?, ?, ?, ?, ?)",
            (evento["placa"], evento["tipo"], evento["metodo"], zona, evento["timestamp"]),
        )
    conn.commit()
    conn.close()
    n = len(cola)
    os.remove(COLA_PATH)
    return n


def validar_manual(placa: str):
    placa = placa.strip().upper()
    cache = _leer_cache()
    registro = cache.get(placa)

    if registro is None:
        print(f"INVÁLIDO — {placa} no está en el caché local de placas autorizadas")
        return False
    if not registro["activo"]:
        print(f"INVÁLIDO — {placa} está inactiva")
        return False

    tipo = "salida" if ultimo_tipo_registro(placa) == "entrada" else "entrada"
    _encolar(placa, tipo)
    print(f"VÁLIDO (modo contingencia) — {placa} ({registro['nombre']}) — {tipo.upper()}")
    print("Registro encolado; se sincronizará automáticamente cuando vuelva la red.")
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 app/contingency.py <PLACA>")
        raise SystemExit(1)
    validar_manual(sys.argv[1])
