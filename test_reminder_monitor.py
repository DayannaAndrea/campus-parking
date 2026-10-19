"""
Script para monitorear el sistema de recordatorios en tiempo real.
Verifica si la reserva de prueba recibe su recordatorio.
"""
import time
from datetime import datetime
from app.db import get_conn

def check_reservation_status():
    """Verifica el estado de la reserva de prueba."""
    conn = get_conn()
    reserva = conn.execute(
        "SELECT * FROM reservas WHERE placa = 'TEST-999' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    if reserva:
        return {
            'placa': reserva['placa'],
            'zona': reserva['zona'],
            'hora_inicio': reserva['hora_inicio'],
            'recordatorio_enviado': reserva['recordatorio_enviado'],
            'estado': reserva['estado']
        }
    return None

def monitor_reminder(duration_seconds=120):
    """
    Monitorea el sistema por X segundos esperando que se envíe el recordatorio.

    Args:
        duration_seconds: Tiempo total de monitoreo (default 2 minutos)
    """
    print("=" * 70)
    print("MONITOR DE RECORDATORIOS - M3-06")
    print("=" * 70)
    print(f"Inicio del monitoreo: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Duracion: {duration_seconds} segundos")
    print("=" * 70)

    start_time = time.time()
    last_status = None
    check_count = 0

    while time.time() - start_time < duration_seconds:
        check_count += 1
        current_time = datetime.now().strftime('%H:%M:%S')

        status = check_reservation_status()

        if status:
            # Si el estado cambió, mostrar actualización
            if status != last_status:
                print(f"\n[{current_time}] Check #{check_count}")
                print(f"  Placa: {status['placa']}")
                print(f"  Zona: {status['zona']}")
                print(f"  Hora inicio: {status['hora_inicio']}")
                print(f"  Estado: {status['estado']}")
                print(f"  Recordatorio enviado: {'SI' if status['recordatorio_enviado'] else 'NO'}")

                # Si se envió el recordatorio, ¡éxito!
                if status['recordatorio_enviado'] and not (last_status and last_status['recordatorio_enviado']):
                    print("\n" + "=" * 70)
                    print("SUCCESS! RECORDATORIO ENVIADO!")
                    print("=" * 70)
                    print(f"Tiempo transcurrido: {int(time.time() - start_time)} segundos")
                    print("\nEl sistema funciona correctamente:")
                    print("  1. Scheduler detectó la reserva en la ventana de 15 min")
                    print("  2. Lógica de negocio ejecutada: obtener_reservas_proximas()")
                    print("  3. Email enviado (simulado o real según configuración)")
                    print("  4. Base de datos actualizada: recordatorio_enviado = 1")
                    print("=" * 70)
                    return True

                last_status = status
        else:
            print(f"\n[{current_time}] Check #{check_count} - Reserva no encontrada")

        # Esperar 5 segundos entre checks
        time.sleep(5)

    print("\n" + "=" * 70)
    print("MONITOREO FINALIZADO")
    print("=" * 70)
    if last_status and last_status['recordatorio_enviado']:
        print("RESULTADO: Recordatorio enviado exitosamente!")
        return True
    else:
        print("RESULTADO: Recordatorio aún no enviado.")
        print("\nPosibles razones:")
        print("  - La reserva aún no entró en la ventana de 15±2 minutos")
        print("  - El scheduler necesita más tiempo (ejecuta cada 1 minuto)")
        print(f"  - Hora de inicio reserva: {last_status['hora_inicio'] if last_status else 'N/A'}")
        print(f"  - Hora actual: {datetime.now().strftime('%H:%M:%S')}")
        return False

if __name__ == "__main__":
    import sys
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    success = monitor_reminder(duration)
    sys.exit(0 if success else 1)
