"""
Tests para M3-06: Sistema de recordatorios por email.

Cobertura:
- Configuración de email
- Obtención de reservas próximas
- Envío de recordatorios
- Tracking de recordatorios enviados
- Templates de email
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from app.db import get_conn
from app.email_service import EmailConfig
from app.reservations import (
    obtener_reservas_proximas,
    enviar_recordatorio_reserva,
    procesar_recordatorios,
    crear_reserva,
)
from app.email_templates import template_recordatorio_reserva, template_recordatorio_texto


@pytest.fixture
def reserva_proxima(bd_temporal, reloj_fijo):
    """Crea una reserva que debe recibir recordatorio en 15 minutos."""
    # Fijar el tiempo para que las pruebas sean deterministas
    ahora = datetime(2026, 9, 22, 10, 0, 0)
    reloj_fijo(ahora)

    conn = get_conn()

    # Crear usuario
    conn.execute(
        "INSERT INTO usuarios (nombre, placa, rol, token) VALUES (?, ?, ?, ?)",
        ("Test Usuario", "ABC123", "estudiante", "token123"),
    )

    # Crear reserva para dentro de 15 minutos exactos
    inicio = ahora + timedelta(minutes=15)
    fin = inicio + timedelta(hours=2)

    conn.execute(
        """INSERT INTO reservas (placa, zona, fecha, hora_inicio, hora_fin, estado, creada, recordatorio_enviado)
           VALUES (?, ?, ?, ?, ?, 'activa', ?, 0)""",
        (
            "ABC123",
            "Zona A",
            inicio.strftime("%Y-%m-%d"),
            inicio.strftime("%H:%M"),
            fin.strftime("%H:%M"),
            ahora.isoformat(timespec="seconds"),
        ),
    )
    conn.commit()

    reserva_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    conn.close()
    return reserva_id


def test_obtener_reservas_proximas_vacia(bd_temporal):
    """Sin reservas próximas, debe retornar lista vacía."""
    proximas = obtener_reservas_proximas()
    assert proximas == []


def test_obtener_reservas_proximas_con_reserva(reserva_proxima):
    """Debe detectar reservas en la ventana de 15 minutos."""
    proximas = obtener_reservas_proximas()
    assert len(proximas) >= 1  # Puede haber otras reservas de otros tests
    # Verificar que nuestra reserva está incluida
    placas = [r["placa"] for r in proximas]
    assert "ABC123" in placas

    # Encontrar nuestra reserva específica
    nuestra_reserva = [r for r in proximas if r["placa"] == "ABC123"][0]
    assert nuestra_reserva["zona"] == "Zona A"
    assert nuestra_reserva["nombre"] == "Test Usuario"
    assert nuestra_reserva["recordatorio_enviado"] == 0


def test_obtener_reservas_proximas_no_incluye_ya_enviados(reserva_proxima):
    """No debe incluir reservas con recordatorio ya enviado."""
    conn = get_conn()
    conn.execute("UPDATE reservas SET recordatorio_enviado = 1 WHERE id = ?", (reserva_proxima,))
    conn.commit()
    conn.close()

    proximas = obtener_reservas_proximas()
    placas = [r["placa"] for r in proximas]
    assert "ABC123" not in placas


def test_obtener_reservas_proximas_no_incluye_lejanas(bd_temporal):
    """No debe incluir reservas que están muy lejos en el tiempo."""
    conn = get_conn()
    conn.execute(
        "INSERT INTO usuarios (nombre, placa, rol, token) VALUES (?, ?, ?, ?)",
        ("Test Usuario", "XYZ789", "profesor", "token456"),
    )

    # Reserva para dentro de 2 horas (fuera de ventana de 15 min)
    ahora = datetime.now()
    inicio = ahora + timedelta(hours=2)
    fin = inicio + timedelta(hours=2)

    conn.execute(
        """INSERT INTO reservas (placa, zona, fecha, hora_inicio, hora_fin, estado, creada, recordatorio_enviado)
           VALUES (?, ?, ?, ?, ?, 'activa', ?, 0)""",
        (
            "XYZ789",
            "Zona B",
            inicio.strftime("%Y-%m-%d"),
            inicio.strftime("%H:%M"),
            fin.strftime("%H:%M"),
            ahora.isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    conn.close()

    proximas = obtener_reservas_proximas()
    placas = [r["placa"] for r in proximas]
    assert "XYZ789" not in placas


@patch("app.reservations.enviar_email")
def test_enviar_recordatorio_reserva_marca_como_enviado(mock_enviar, reserva_proxima):
    """Debe marcar la reserva como recordatorio_enviado = 1 tras enviar."""
    mock_enviar.return_value = True

    resultado = enviar_recordatorio_reserva(reserva_proxima)
    assert resultado is True

    conn = get_conn()
    reserva = conn.execute("SELECT * FROM reservas WHERE id = ?", (reserva_proxima,)).fetchone()
    conn.close()

    assert reserva["recordatorio_enviado"] == 1
    # Verificar que se llamó enviar_email
    assert mock_enviar.called


@patch("app.reservations.enviar_email")
def test_procesar_recordatorios_envia_multiples(mock_enviar, bd_temporal, reloj_fijo):
    """Debe procesar y enviar múltiples recordatorios en una sola ejecución."""
    mock_enviar.return_value = True

    # Fijar el tiempo
    ahora = datetime(2026, 9, 22, 10, 0, 0)
    reloj_fijo(ahora)

    # Crear 3 reservas próximas
    conn = get_conn()
    inicio = ahora + timedelta(minutes=15)  # Exactamente 15 minutos
    fin = inicio + timedelta(hours=1)

    for i, placa in enumerate(["AAA111", "BBB222", "CCC333"]):
        conn.execute(
            "INSERT INTO usuarios (nombre, placa, rol, token) VALUES (?, ?, ?, ?)",
            (f"Usuario {i+1}", placa, "estudiante", f"token{i+1}"),
        )
        conn.execute(
            """INSERT INTO reservas (placa, zona, fecha, hora_inicio, hora_fin, estado, creada, recordatorio_enviado)
               VALUES (?, ?, ?, ?, ?, 'activa', ?, 0)""",
            (
                placa,
                "Zona A",
                inicio.strftime("%Y-%m-%d"),
                inicio.strftime("%H:%M"),
                fin.strftime("%H:%M"),
                ahora.isoformat(timespec="seconds"),
            ),
        )
    conn.commit()
    conn.close()

    enviados = procesar_recordatorios()
    assert enviados == 3
    assert mock_enviar.call_count == 3


def test_template_recordatorio_texto_incluye_datos():
    """El template de texto debe incluir todos los datos de la reserva."""
    texto = template_recordatorio_texto(
        nombre="Juan Pérez",
        placa="ABC-123",
        zona="Zona A",
        fecha="2026-09-22",
        hora_inicio="08:00",
        hora_fin="10:00",
    )

    assert "Juan Pérez" in texto
    assert "ABC-123" in texto
    assert "Zona A" in texto
    assert "2026-09-22" in texto
    assert "08:00" in texto
    assert "10:00" in texto
    assert "15 minutos" in texto


def test_template_recordatorio_html_es_valido():
    """El template HTML debe ser HTML válido con todos los datos."""
    html = template_recordatorio_reserva(
        nombre="María González",
        placa="XYZ-789",
        zona="Zona B",
        fecha="2026-09-22",
        hora_inicio="14:00",
        hora_fin="16:00",
    )

    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html
    assert "María González" in html
    assert "XYZ-789" in html
    assert "Zona B" in html
    assert "14:00" in html
    assert "16:00" in html
    # Verificar estilos CSS incluidos
    assert "background" in html
    assert "color" in html


def test_template_html_formatea_fecha():
    """El template HTML debe formatear la fecha de forma legible."""
    html = template_recordatorio_reserva(
        nombre="Test",
        placa="TEST-001",
        zona="Zona C",
        fecha="2026-01-05",  # Lunes
        hora_inicio="09:00",
        hora_fin="11:00",
    )

    # Debe incluir día de la semana (2026-01-05 es lunes)
    assert "Lunes" in html or "lunes" in html.lower()
    # Debe incluir fecha en formato DD/MM/YYYY
    assert "05/01/2026" in html


def test_reserva_sin_recordatorio_tras_crear(bd_temporal):
    """Al crear una reserva, recordatorio_enviado debe ser 0."""
    conn = get_conn()
    conn.execute(
        "INSERT INTO usuarios (nombre, placa, rol, token) VALUES (?, ?, ?, ?)",
        ("Test", "TEST123", "estudiante", "token_test"),
    )
    conn.commit()
    conn.close()

    manana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    crear_reserva("TEST123", "Zona A", manana, "08:00", "10:00")

    conn = get_conn()
    reserva = conn.execute("SELECT * FROM reservas WHERE placa = 'TEST123'").fetchone()
    conn.close()

    assert reserva is not None
    assert reserva["recordatorio_enviado"] == 0


def test_email_config_defaults():
    """Verifica los valores por defecto de EmailConfig."""
    # Los valores por defecto deben estar configurados
    assert EmailConfig.SMTP_HOST is not None
    assert EmailConfig.SMTP_PORT > 0
    assert EmailConfig.FROM_EMAIL is not None
