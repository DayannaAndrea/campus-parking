"""
Historia M3-06: Templates HTML para emails de recordatorio.

Plantillas profesionales y responsivas para notificaciones por correo.
"""


def template_recordatorio_reserva(nombre: str, placa: str, zona: str, fecha: str,
                                   hora_inicio: str, hora_fin: str) -> str:
    """
    Genera el HTML del email de recordatorio de reserva.

    Args:
        nombre: Nombre del usuario
        placa: Placa del vehículo
        zona: Zona reservada
        fecha: Fecha de la reserva (YYYY-MM-DD)
        hora_inicio: Hora de inicio (HH:MM)
        hora_fin: Hora de fin (HH:MM)

    Returns:
        HTML del email
    """
    # Formatear fecha legible
    from datetime import datetime
    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
    fecha_legible = fecha_obj.strftime("%d/%m/%Y")
    dia_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][fecha_obj.weekday()]

    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recordatorio de Reserva - Campus Parking</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .icon {{
            font-size: 48px;
            margin-bottom: 10px;
        }}
        .content {{
            padding: 30px 20px;
        }}
        .greeting {{
            font-size: 16px;
            margin-bottom: 20px;
            color: #555;
        }}
        .alert-box {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .alert-box strong {{
            color: #856404;
        }}
        .details {{
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .detail-row {{
            display: flex;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        .detail-row:last-child {{
            border-bottom: none;
        }}
        .detail-icon {{
            font-size: 24px;
            margin-right: 15px;
            min-width: 30px;
        }}
        .detail-label {{
            font-weight: 600;
            color: #666;
            margin-right: 10px;
        }}
        .detail-value {{
            color: #333;
            font-size: 16px;
        }}
        .warning {{
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 6px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
        }}
        .warning-text {{
            color: #856404;
            font-size: 14px;
            margin: 0;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            font-size: 12px;
            border-top: 1px solid #e9ecef;
        }}
        .footer-logo {{
            font-size: 18px;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">🅿️</div>
            <h1>Recordatorio de Reserva</h1>
        </div>

        <div class="content">
            <div class="greeting">
                Hola <strong>{nombre}</strong>,
            </div>

            <div class="alert-box">
                <strong>⏰ Tu reserva de parqueadero comienza en 15 minutos</strong>
            </div>

            <p>Este es un recordatorio de tu reserva activa en el parqueadero institucional:</p>

            <div class="details">
                <div class="detail-row">
                    <div class="detail-icon">📍</div>
                    <div>
                        <span class="detail-label">Zona:</span>
                        <span class="detail-value">{zona}</span>
                    </div>
                </div>

                <div class="detail-row">
                    <div class="detail-icon">📅</div>
                    <div>
                        <span class="detail-label">Fecha:</span>
                        <span class="detail-value">{dia_semana}, {fecha_legible}</span>
                    </div>
                </div>

                <div class="detail-row">
                    <div class="detail-icon">⏰</div>
                    <div>
                        <span class="detail-label">Horario:</span>
                        <span class="detail-value">{hora_inicio} - {hora_fin}</span>
                    </div>
                </div>

                <div class="detail-row">
                    <div class="detail-icon">🚗</div>
                    <div>
                        <span class="detail-label">Placa:</span>
                        <span class="detail-value">{placa}</span>
                    </div>
                </div>
            </div>

            <div class="warning">
                <p class="warning-text">
                    ⚠️ <strong>IMPORTANTE:</strong> Si no ingresas dentro de los primeros 15 minutos
                    de tu franja horaria, la reserva se liberará automáticamente para otros usuarios.
                </p>
            </div>

            <p style="margin-top: 20px; color: #666;">
                Recuerda tener tu código QR listo para el escaneo en portería.
            </p>

            <p style="color: #666;">
                ¡Nos vemos pronto! 👋
            </p>
        </div>

        <div class="footer">
            <div class="footer-logo">🅿️ Campus Parking</div>
            <div>Sistema de Control de Entradas y Cupos</div>
            <div style="margin-top: 10px; color: #999;">
                Este es un correo automático, por favor no responder.
            </div>
        </div>
    </div>
</body>
</html>
    """
    return html.strip()


def template_recordatorio_texto(nombre: str, placa: str, zona: str, fecha: str,
                                 hora_inicio: str, hora_fin: str) -> str:
    """
    Genera la versión de texto plano del recordatorio (para clientes sin HTML).

    Args:
        nombre: Nombre del usuario
        placa: Placa del vehículo
        zona: Zona reservada
        fecha: Fecha de la reserva
        hora_inicio: Hora de inicio
        hora_fin: Hora de fin

    Returns:
        Texto plano del email
    """
    return f"""
Hola {nombre},

⏰ RECORDATORIO: Tu reserva de parqueadero comienza en 15 minutos

Detalles de tu reserva:

📍 Zona: {zona}
📅 Fecha: {fecha}
⏰ Horario: {hora_inicio} - {hora_fin}
🚗 Placa: {placa}

⚠️ IMPORTANTE: Si no ingresas dentro de los primeros 15 minutos de tu franja
horaria, la reserva se liberará automáticamente para otros usuarios.

Recuerda tener tu código QR listo para el escaneo en portería.

¡Nos vemos pronto!

---
🅿️ Campus Parking
Sistema de Control de Entradas y Cupos
Este es un correo automático, por favor no responder.
    """.strip()


def template_confirmacion_reserva(nombre: str, placa: str, zona: str, fecha: str,
                                   hora_inicio: str, hora_fin: str) -> str:
    """
    Genera el HTML del email de confirmación de reserva.

    Args:
        nombre: Nombre del usuario
        placa: Placa del vehículo
        zona: Zona reservada
        fecha: Fecha de la reserva (YYYY-MM-DD)
        hora_inicio: Hora de inicio (HH:MM)
        hora_fin: Hora de fin (HH:MM)

    Returns:
        HTML del email de confirmación
    """
    # Formatear fecha legible
    from datetime import datetime
    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
    fecha_legible = fecha_obj.strftime("%d/%m/%Y")
    dia_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][fecha_obj.weekday()]

    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Confirmación de Reserva - Campus Parking</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .icon {{
            font-size: 48px;
            margin-bottom: 10px;
        }}
        .content {{
            padding: 30px 20px;
        }}
        .greeting {{
            font-size: 16px;
            margin-bottom: 20px;
            color: #555;
        }}
        .success-box {{
            background-color: #d4edda;
            border-left: 4px solid #28a745;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .success-box strong {{
            color: #155724;
        }}
        .details {{
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .detail-row {{
            display: flex;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        .detail-row:last-child {{
            border-bottom: none;
        }}
        .detail-icon {{
            font-size: 24px;
            margin-right: 15px;
            min-width: 30px;
        }}
        .detail-label {{
            font-weight: 600;
            color: #666;
            margin-right: 10px;
        }}
        .detail-value {{
            color: #333;
            font-size: 16px;
        }}
        .info-box {{
            background-color: #e7f3ff;
            border: 1px solid #2196f3;
            border-radius: 6px;
            padding: 15px;
            margin: 20px 0;
        }}
        .info-text {{
            color: #004085;
            font-size: 14px;
            margin: 5px 0;
        }}
        .reminder-box {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .reminder-text {{
            color: #856404;
            font-size: 14px;
            margin: 0;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            font-size: 12px;
            border-top: 1px solid #e9ecef;
        }}
        .footer-logo {{
            font-size: 18px;
            font-weight: 600;
            color: #28a745;
            margin-bottom: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">✅</div>
            <h1>¡Reserva Confirmada!</h1>
        </div>

        <div class="content">
            <div class="greeting">
                Hola <strong>{nombre}</strong>,
            </div>

            <div class="success-box">
                <strong>✓ Tu reserva de parqueadero ha sido confirmada exitosamente</strong>
            </div>

            <p>Hemos registrado tu reserva con los siguientes detalles:</p>

            <div class="details">
                <div class="detail-row">
                    <div class="detail-icon">📍</div>
                    <div>
                        <span class="detail-label">Zona:</span>
                        <span class="detail-value">{zona}</span>
                    </div>
                </div>

                <div class="detail-row">
                    <div class="detail-icon">📅</div>
                    <div>
                        <span class="detail-label">Fecha:</span>
                        <span class="detail-value">{dia_semana}, {fecha_legible}</span>
                    </div>
                </div>

                <div class="detail-row">
                    <div class="detail-icon">⏰</div>
                    <div>
                        <span class="detail-label">Horario:</span>
                        <span class="detail-value">{hora_inicio} - {hora_fin}</span>
                    </div>
                </div>

                <div class="detail-row">
                    <div class="detail-icon">🚗</div>
                    <div>
                        <span class="detail-label">Placa:</span>
                        <span class="detail-value">{placa}</span>
                    </div>
                </div>
            </div>

            <div class="info-box">
                <p class="info-text">
                    <strong>📧 Recordatorio automático:</strong>
                </p>
                <p class="info-text">
                    Recibirás un correo de recordatorio 15 minutos antes de tu hora de inicio.
                </p>
            </div>

            <div class="reminder-box">
                <p class="reminder-text">
                    <strong>⚠️ Importante:</strong> Debes ingresar dentro de los primeros 15 minutos
                    de tu franja horaria. Si no lo haces, la reserva se liberará automáticamente.
                </p>
            </div>

            <p style="margin-top: 20px; color: #666;">
                <strong>Próximos pasos:</strong>
            </p>
            <ul style="color: #666;">
                <li>Ten tu código QR listo para el escaneo en portería</li>
                <li>Llega con tiempo suficiente</li>
                <li>Dirígete directamente a la <strong>{zona}</strong></li>
            </ul>

            <p style="color: #666;">
                ¡Te esperamos! 🚗💨
            </p>
        </div>

        <div class="footer">
            <div class="footer-logo">🅿️ Campus Parking</div>
            <div>Sistema de Control de Entradas y Cupos</div>
            <div style="margin-top: 10px; color: #999;">
                Este es un correo automático, por favor no responder.
            </div>
        </div>
    </div>
</body>
</html>
    """
    return html.strip()


def template_confirmacion_texto(nombre: str, placa: str, zona: str, fecha: str,
                                hora_inicio: str, hora_fin: str) -> str:
    """
    Genera la versión de texto plano de la confirmación de reserva.

    Args:
        nombre: Nombre del usuario
        placa: Placa del vehículo
        zona: Zona reservada
        fecha: Fecha de la reserva
        hora_inicio: Hora de inicio
        hora_fin: Hora de fin

    Returns:
        Texto plano del email de confirmación
    """
    return f"""
Hola {nombre},

✅ ¡RESERVA CONFIRMADA!

Tu reserva de parqueadero ha sido registrada exitosamente.

Detalles de tu reserva:

📍 Zona: {zona}
📅 Fecha: {fecha}
⏰ Horario: {hora_inicio} - {hora_fin}
🚗 Placa: {placa}

📧 Recordatorio automático:
Recibirás un correo 15 minutos antes de tu hora de inicio.

⚠️ IMPORTANTE: Debes ingresar dentro de los primeros 15 minutos de tu
franja horaria. Si no lo haces, la reserva se liberará automáticamente.

Próximos pasos:
- Ten tu código QR listo para el escaneo en portería
- Llega con tiempo suficiente
- Dirígete directamente a la {zona}

¡Te esperamos! 🚗💨

---
🅿️ Campus Parking
Sistema de Control de Entradas y Cupos
Este es un correo automático, por favor no responder.
    """.strip()
