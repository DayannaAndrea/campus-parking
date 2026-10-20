"""
Autenticación: contraseña de conductores y cuentas fijas del personal.

- Conductores: la contraseña se guarda cifrada (hash) en usuarios.password_hash.
- Personal: dos cuentas fijas, 'admin' y 'porteria', cuyas contraseñas viven en
  el .env (ADMIN_PASSWORD, PORTERIA_PASSWORD). Si la variable está vacía, esa
  cuenta queda deshabilitada.
"""
import hmac
import os

from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_conn

MIN_CLAVE = 8
CUENTAS_PERSONAL = {"admin": "ADMIN_PASSWORD", "porteria": "PORTERIA_PASSWORD"}


def validar_clave_nueva(clave: str, confirmacion: str) -> None:
    if len(clave or "") < MIN_CLAVE:
        raise ValueError(f"La contraseña debe tener al menos {MIN_CLAVE} caracteres.")
    if clave != confirmacion:
        raise ValueError("Las contraseñas no coinciden.")


def datos_placa(placa: str):
    conn = get_conn()
    fila = conn.execute(
        "SELECT email, password_hash FROM usuarios WHERE placa = ?", (placa.strip().upper(),)
    ).fetchone()
    conn.close()
    return fila


def guardar_clave(placa: str, clave: str) -> None:
    conn = get_conn()
    conn.execute(
        "UPDATE usuarios SET password_hash = ? WHERE placa = ?",
        (generate_password_hash(clave), placa.strip().upper()),
    )
    conn.commit()
    conn.close()


def verificar_conductor(email: str, clave: str):
    """Devuelve el usuario si el correo y la contraseña coinciden; si no, None.

    Un mismo correo puede tener varios vehículos: se acepta el que coincida.
    """
    conn = get_conn()
    filas = conn.execute(
        "SELECT nombre, placa, email, password_hash FROM usuarios WHERE LOWER(email) = ?",
        ((email or "").strip().lower(),),
    ).fetchall()
    conn.close()
    for fila in filas:
        if fila["password_hash"] and check_password_hash(fila["password_hash"], clave or ""):
            return fila
    return None


def tiene_cuenta_sin_clave(email: str) -> bool:
    """True si el correo existe pero ninguno de sus vehículos tiene contraseña (registro antiguo)."""
    conn = get_conn()
    filas = conn.execute(
        "SELECT password_hash FROM usuarios WHERE LOWER(email) = ?", ((email or "").strip().lower(),)
    ).fetchall()
    conn.close()
    return bool(filas) and not any(f["password_hash"] for f in filas)


def verificar_personal(usuario: str, clave: str) -> bool:
    variable = CUENTAS_PERSONAL.get(usuario)
    esperada = os.getenv(variable, "") if variable else ""
    if not esperada or not clave:
        return False
    return hmac.compare_digest(clave.encode("utf-8"), esperada.encode("utf-8"))
