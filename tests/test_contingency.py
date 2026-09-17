import json

from app import contingency as cont
from app.db import get_conn
from app.entry_log import registrar_evento
from app.qr_generator import generar_qr


def test_validar_manual_placa_autorizada_en_cache(bd_temporal):
    generar_qr("Ana", "ABC123", "estudiante")
    assert cont.validar_manual("ABC123") is True
    assert cont.validar_manual("abc123") is True  # normaliza mayúsculas


def test_validar_manual_placa_no_autorizada(bd_temporal):
    assert cont.validar_manual("ZZZ999") is False


def test_sincronizar_cola_vacia_y_deriva_zona_de_salida(bd_temporal):
    generar_qr("Ana", "ABC123", "estudiante")
    registrar_evento("ABC123", "qr", "Zona A")
    cola = [
        {"placa": "ABC123", "tipo": "salida", "metodo": "contingencia", "timestamp": "2026-01-01T12:00:00"},
        {"placa": "DEF456", "tipo": "entrada", "metodo": "contingencia", "timestamp": "2026-01-01T12:01:00"},
    ]
    with open(cont.COLA_PATH, "w") as f:
        json.dump(cola, f)

    assert cont.sincronizar_cola() == 2
    import os
    assert not os.path.exists(cont.COLA_PATH)

    filas = get_conn().execute(
        "SELECT * FROM registros WHERE metodo = 'contingencia' ORDER BY id").fetchall()
    assert len(filas) == 2
    assert filas[0]["tipo"] == "salida"
    assert filas[0]["zona"] == "Zona A"  # derivada del último ingreso


def test_sincronizar_cola_sin_archivo_es_noop(bd_temporal):
    assert cont.sincronizar_cola() == 0