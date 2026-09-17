from app.entry_log import registrar_evento
from app.qr_generator import generar_qr
from app.zones import listar_zonas, panel_cupos


def test_seed_de_tres_zonas(bd_temporal):
    assert [z["nombre"] for z in listar_zonas()] == ["Zona A", "Zona B", "Zona C"]


def test_panel_cupos_refleja_ocupacion(bd_temporal):
    generar_qr("Ana", "ABC123", "estudiante")
    registrar_evento("ABC123", "qr", "Zona A")
    zona_a = next(z for z in panel_cupos() if z["zona"] == "Zona A")
    assert zona_a["ocupados"] == 1
    assert zona_a["disponibles"] == 99
    assert zona_a["alerta_llena"] is False
    assert zona_a["porcentaje"] == 1