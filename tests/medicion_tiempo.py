"""
Historia M1-05 — Prueba en portería con medición real del tiempo de ingreso.

Este script complementa el checklist manual (checklist_prueba_porteria.md):
simula el paso de N vehículos por el validador para medir la latencia de
software del sistema (no reemplaza la prueba con usuarios reales, que se
documenta en el checklist).
"""
import os
import sys
import time
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.qr_generator import generar_qr  # noqa: E402
from app.validator import escanear  # noqa: E402

NOMBRES = [f"Usuario Demo {i}" for i in range(1, 11)]
ROLES = ["estudiante", "profesor", "administrativo"]


def ejecutar_prueba(n_vehiculos: int = 10):
    tiempos = []
    for i in range(n_vehiculos):
        placa = f"DEMO{i:03d}"
        ruta = generar_qr(NOMBRES[i % len(NOMBRES)], placa, ROLES[i % len(ROLES)])

        inicio = time.perf_counter()
        escanear(ruta)
        tiempos.append(time.perf_counter() - inicio)

    promedio_ms = statistics.mean(tiempos) * 1000
    print("\n=== Resultado de la prueba de latencia de software ===")
    print(f"Vehículos simulados: {n_vehiculos}")
    print(f"Tiempo promedio de validación por vehículo: {promedio_ms:.1f} ms")
    print("Nota: este tiempo es solo la latencia del software (escaneo +")
    print("consulta a BD), no el tiempo real de ingreso del vehículo, que")
    print("depende también de la maniobra física en portería. El tiempo")
    print("real de ingreso se mide con el checklist_prueba_porteria.md.")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    ejecutar_prueba(n)
