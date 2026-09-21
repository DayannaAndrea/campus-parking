"""
Historia M3-06: Scheduler para recordatorios automáticos.

Ejecuta procesar_recordatorios() cada minuto en segundo plano.
Usa APScheduler para tareas periódicas sin bloquear Flask.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime


# Instancia global del scheduler
_scheduler = None


def job_procesar_recordatorios():
    """Job que ejecuta el scheduler cada minuto."""
    # Importación tardía para evitar ciclos de importación
    from app.reservations import procesar_recordatorios

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Ejecutando job de recordatorios...")
    try:
        enviados = procesar_recordatorios()
        if enviados > 0:
            print(f"[OK] Se enviaron {enviados} recordatorios")
    except Exception as e:
        print(f"[ERROR] Error en job de recordatorios: {e}")


def iniciar_scheduler():
    """Inicia el scheduler de recordatorios."""
    global _scheduler

    if _scheduler is not None:
        print("[WARNING] Scheduler ya iniciado")
        return

    _scheduler = BackgroundScheduler()

    # Job: ejecutar cada minuto
    _scheduler.add_job(
        func=job_procesar_recordatorios,
        trigger="interval",
        minutes=1,
        id="recordatorios_reservas",
        name="Procesar recordatorios de reservas",
        replace_existing=True,
    )

    _scheduler.start()
    print("[OK] Scheduler iniciado: recordatorios cada 1 minuto")


def detener_scheduler():
    """Detiene el scheduler de forma limpia."""
    global _scheduler

    if _scheduler is not None:
        _scheduler.shutdown()
        _scheduler = None
        print("[STOP] Scheduler detenido")


def estado_scheduler() -> dict:
    """Obtiene el estado actual del scheduler."""
    if _scheduler is None:
        return {"activo": False, "jobs": []}

    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "nombre": job.name,
            "proxima_ejecucion": job.next_run_time.isoformat() if job.next_run_time else None,
        })

    return {
        "activo": _scheduler.running,
        "jobs": jobs,
    }
