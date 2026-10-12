"""
Protección CSRF para los formularios de la app.

Usa un token por sesión almacenado en la cookie de sesión de Flask.
Se puede desactivar con la variable de entorno CSRF_OFF=1 (modo pruebas).
"""
import hmac
import secrets

from flask import abort, request, session


def generar_token() -> str:
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_hex(32)
        session["_csrf_token"] = token
    return token


def validar_csrf():
    """Aborta con 400 si una petición POST no trae un token CSRF válido."""
    from flask import current_app

    if current_app.config.get("CSRF_OFF"):
        return
    token = session.get("_csrf_token")
    enviado = request.form.get("csrf_token") or request.headers.get("X-CSRFToken", "")
    if not token or not enviado or not hmac.compare_digest(token, enviado):
        abort(400, description="Token CSRF inválido. Recarga la página y vuelve a intentarlo.")