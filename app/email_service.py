"""
Historia M3-06: Recordatorio de reserva por correo institucional.

Sistema de notificación por correo electrónico usando SMTP.
Envía recordatorios 15 minutos antes del inicio de una reserva.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional


class EmailConfig:
    """Configuración del servidor SMTP y credenciales."""

    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@campus-parking.edu")
    FROM_NAME = os.getenv("FROM_NAME", "Campus Parking")

    @classmethod
    def is_configured(cls) -> bool:
        """Verifica si el servicio de email está configurado."""
        return bool(cls.SMTP_USER and cls.SMTP_PASSWORD)


def enviar_email(
    destinatario: str,
    asunto: str,
    cuerpo_texto: str,
    cuerpo_html: Optional[str] = None
) -> bool:
    """
    Envía un correo electrónico usando SMTP.

    Args:
        destinatario: Email del destinatario
        asunto: Asunto del correo
        cuerpo_texto: Contenido en texto plano
        cuerpo_html: Contenido en HTML (opcional)

    Returns:
        True si se envió correctamente, False en caso contrario
    """
    if not EmailConfig.is_configured():
        print("[WARNING] Email no configurado. Set SMTP_USER y SMTP_PASSWORD en variables de entorno.")
        return False

    try:
        # Crear mensaje
        mensaje = MIMEMultipart("alternative")
        mensaje["Subject"] = asunto
        mensaje["From"] = f"{EmailConfig.FROM_NAME} <{EmailConfig.FROM_EMAIL}>"
        mensaje["To"] = destinatario

        # Agregar versión texto plano
        parte_texto = MIMEText(cuerpo_texto, "plain", "utf-8")
        mensaje.attach(parte_texto)

        # Agregar versión HTML si existe
        if cuerpo_html:
            parte_html = MIMEText(cuerpo_html, "html", "utf-8")
            mensaje.attach(parte_html)

        # Conectar y enviar
        with smtplib.SMTP(EmailConfig.SMTP_HOST, EmailConfig.SMTP_PORT) as servidor:
            servidor.starttls()
            servidor.login(EmailConfig.SMTP_USER, EmailConfig.SMTP_PASSWORD)
            servidor.send_message(mensaje)

        print(f"[OK] Email enviado a {destinatario}: {asunto}")
        return True

    except Exception as e:
        print(f"[ERROR] Error enviando email a {destinatario}: {e}")
        return False


def test_email_connection() -> bool:
    """Prueba la conexión al servidor SMTP."""
    if not EmailConfig.is_configured():
        return False

    try:
        with smtplib.SMTP(EmailConfig.SMTP_HOST, EmailConfig.SMTP_PORT) as servidor:
            servidor.starttls()
            servidor.login(EmailConfig.SMTP_USER, EmailConfig.SMTP_PASSWORD)
        print("[OK] Conexion SMTP exitosa")
        return True
    except Exception as e:
        print(f"[ERROR] Error de conexion SMTP: {e}")
        return False
