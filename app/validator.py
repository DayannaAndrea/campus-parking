"""
Historia M1-02 — App/lector para el vigilante.

Como vigilante, quiero escanear el QR en portería y ver de inmediato si el
vehículo puede ingresar.

Criterio de aceptación:
- Decodifica el QR y consulta la base de datos.
- Muestra VÁLIDO (verde) o INVÁLIDO (rojo) en menos de 5 segundos.
- Funciona con imagen de cámara web o con un PNG ya escaneado (para la demo
  de este prototipo, ya que no hay hardware de portería disponible en clase).
"""
import sys
import time
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyzbar_fallback import decode_qr  # decodificador propio (ver más abajo)  # noqa: E402
from app.db import get_conn  # noqa: E402
from app.qr_generator import _firmar  # noqa: E402
from app.entry_log import registrar_evento  # noqa: E402
from app.reservations import reserva_vigente, marcar_reserva_usada  # noqa: E402

VERDE = "\033[92m"
ROJO = "\033[91m"
RESET = "\033[0m"


def validar_token(token: str):
    try:
        placa, id_usuario, firma = token.split("|")
        id_usuario = int(id_usuario)
    except (ValueError, AttributeError):
        return False, "Formato de QR no reconocido"

    if firma != _firmar(placa, id_usuario):
        return False, "Firma inválida (posible QR falsificado)"

    conn = get_conn()
    fila = conn.execute(
        "SELECT * FROM usuarios WHERE id = ? AND placa = ?", (id_usuario, placa)
    ).fetchone()
    conn.close()

    if fila is None:
        return False, "Usuario no registrado"
    if not fila["activo"]:
        return False, "Usuario inactivo / vehículo dado de baja"
    return True, placa


def escanear(ruta_qr: str, zona: str = None):
    inicio = time.perf_counter()
    token = decode_qr(ruta_qr)
    valido, info = validar_token(token) if token else (False, "No se pudo leer el QR")

    duracion = time.perf_counter() - inicio
    resultado = {"valido": valido, "duracion_ms": round(duracion * 1000, 1)}

    if valido:
        placa = info
        reserva = reserva_vigente(placa)  # M3-03
        tipo = registrar_evento(placa, metodo="qr", zona=zona)
        if reserva and tipo == "entrada":
            marcar_reserva_usada(placa, reserva["id"])
        resultado.update({"placa": placa, "tipo": tipo, "reserva": reserva})
        print(f"{VERDE}>>> VÁLIDO — {placa} — {tipo.upper()} registrada{RESET}")
        if reserva:
            print(f"    Reserva vigente: {reserva['hora_inicio']}–{reserva['hora_fin']} en {reserva['zona']}")
    else:
        resultado["mensaje"] = info
        print(f"{ROJO}>>> INVÁLIDO — {info}{RESET}")

    print(f"Tiempo de validación: {duracion*1000:.1f} ms")
    return resultado


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 app/validator.py <ruta_al_qr.png>")
        raise SystemExit(1)
    if not os.path.exists(sys.argv[1]):
        print("El archivo QR no existe. Genera uno primero con app/qr_generator.py")
        raise SystemExit(1)
    escanear(sys.argv[1])
