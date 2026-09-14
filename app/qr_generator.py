"""
Historia M1-01 — Generación del QR por usuario.

Como estudiante/profesor registrado, quiero recibir un código QR único
vinculado a mi vehículo, para poder ingresar sin mostrar papeles.

Criterio de aceptación:
- Al registrarse, el sistema genera un QR único.
- El QR se puede exportar/mostrar desde el celular (PNG).
- El QR queda asociado a placa + usuario en la base de datos.
"""
import hashlib
import hmac
import os
import sys

import qrcode

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db import get_conn, DATA_DIR  # noqa: E402

SECRET_KEY = b"campus-parking-clave-local-demo"  # en producción: variable de entorno


def _firmar(placa: str, id_usuario: int) -> str:
    """Genera un hash corto para que el modo de contingencia pueda validar sin red."""
    msg = f"{placa}|{id_usuario}".encode()
    return hmac.new(SECRET_KEY, msg, hashlib.sha256).hexdigest()[:12]


def generar_qr(nombre: str, placa: str, rol: str) -> str:
    placa = placa.strip().upper()
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO usuarios (nombre, placa, rol, token) VALUES (?, ?, ?, '')",
        (nombre, placa, rol),
    )
    id_usuario = cur.lastrowid
    token = f"{placa}|{id_usuario}|{_firmar(placa, id_usuario)}"
    conn.execute("UPDATE usuarios SET token = ? WHERE id = ?", (token, id_usuario))
    conn.commit()
    conn.close()

    img = qrcode.make(token)
    ruta = os.path.join(DATA_DIR, "qrcodes", f"{placa}.png")
    img.save(ruta)
    return ruta


def _demo():
    print("== M1-01: Generación de QR (demo) ==")
    ruta = generar_qr("Dayanna García", "SMR123", "profesor")
    print(f"QR generado: {ruta}")
    ruta2 = generar_qr("Edwin Ternera", "JHT456", "estudiante")
    print(f"QR generado: {ruta2}")


if __name__ == "__main__":
    _demo()
