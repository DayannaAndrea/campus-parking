from app.entry_log import historial_por_placa, listar_usuarios, registrar_evento
from app.qr_generator import generar_qr
from app.zones import ocupacion_actual


def test_entrada_y_salida_alternan(bd_temporal):
    generar_qr("Ana", "ABC123", "estudiante")
    assert registrar_evento("ABC123", "qr", "Zona A") == "entrada"
    assert registrar_evento("ABC123", "qr", "Zona A") == "salida"
    assert registrar_evento("ABC123", "qr", "Zona A") == "entrada"


def test_salida_libera_la_zona_del_ultimo_ingreso(bd_temporal):
    generar_qr("Ana", "ABC123", "estudiante")
    registrar_evento("ABC123", "qr", "Zona A")
    assert ocupacion_actual("Zona A") == 1

    # El vigilante no elige zona en la salida: debe liberarse la del ingreso.
    registrar_evento("ABC123", "qr")
    assert ocupacion_actual("Zona A") == 0

    salidas = historial_por_placa("ABC123")
    assert salidas[-1]["tipo"] == "salida"
    assert salidas[-1]["zona"] == "Zona A"


def test_historial_y_estado_del_usuario(bd_temporal):
    generar_qr("Ana", "ABC123", "estudiante")
    registrar_evento("ABC123", "qr", "Zona A")
    assert historial_por_placa("ABC123")[0]["tipo"] == "entrada"
    usuarios = listar_usuarios()
    assert usuarios[0]["placa"] == "ABC123"
    assert usuarios[0]["estado"] == "Dentro"