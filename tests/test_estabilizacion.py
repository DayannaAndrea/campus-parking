"""Pruebas de estabilización: casos límite de QR, contingencia y cupos."""
import pytest


def _mk(placa="ABC123", nombre="Ana", rol="estudiante"):
    import app.qr_generator as qg
    return qg.generar_qr(nombre, placa, rol)


def _zona_mini(db, aforo=1):
    c = db.get_conn()
    c.execute("INSERT INTO zonas (nombre, aforo_maximo) VALUES ('Mini', ?)", (aforo,))
    c.commit(); c.close()


def test_qr_se_lee_y_alterna_entrada_salida(bd_temporal):
    from app.validator import escanear
    ruta = _mk()
    assert escanear(ruta, zona="Zona A")["tipo"] == "entrada"
    assert escanear(ruta, zona="Zona A")["tipo"] == "salida"


@pytest.mark.parametrize("placa", ["../../x", "AB", "AB C12", "ABCDEFGH", ""])
def test_placa_con_formato_invalido_se_rechaza(bd_temporal, placa):
    with pytest.raises(ValueError):
        _mk(placa=placa)


def test_registro_web_muestra_error_de_placa(bd_temporal):
    import flask_app
    c = flask_app.app.test_client()
    r = c.post("/registro", data={"nombre": "A", "placa": "AB", "rol": "estudiante"})
    assert r.status_code == 200 and b"5 y 7" in r.data


def test_vigilante_no_permite_path_traversal(bd_temporal):
    import flask_app
    c = flask_app.app.test_client()
    r = c.post("/vigilante", data={"placa": "../../etc/passwd"})
    assert r.status_code == 200 and b"root:" not in r.data


def test_contingencia_alterna_con_cola_pendiente(bd_temporal):
    from app.contingency import validar_manual, sincronizar_cola
    from app.entry_log import historial_por_placa
    _mk()
    validar_manual("ABC123"); validar_manual("ABC123")
    sincronizar_cola()
    assert [h["tipo"] for h in historial_por_placa("ABC123")] == ["entrada", "salida"]


def test_no_se_puede_entrar_a_zona_llena(bd_temporal):
    from app.validator import escanear
    _zona_mini(bd_temporal)
    assert escanear(_mk(placa="AAA111"), zona="Mini")["valido"] is True
    r = escanear(_mk(placa="BBB222"), zona="Mini")
    assert r["valido"] is False and "llena" in r["mensaje"].lower()


def test_quien_esta_dentro_puede_salir_aunque_la_zona_este_llena(bd_temporal):
    from app.validator import escanear
    _zona_mini(bd_temporal)
    ruta = _mk(placa="AAA111")
    escanear(ruta, zona="Mini")
    assert escanear(ruta, zona="Mini")["tipo"] == "salida"
