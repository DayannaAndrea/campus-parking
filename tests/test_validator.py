import datetime as _dt

from app import reservations as res
from app.db import get_conn
from app.qr_generator import generar_qr
from app.validator import escanear, validar_token


def test_escanear_registra_entrada_y_salida(bd_temporal):
    ruta = generar_qr("Pablo", "JHT999", "profesor")
    r1 = escanear(ruta, zona="Zona B")
    assert r1["valido"] is True
    assert r1["tipo"] == "entrada"

    r2 = escanear(ruta)  # sin zona: la salida debe liberar la del ingreso
    assert r2["valido"] is True
    assert r2["tipo"] == "salida"


def test_validar_token_rechaza_firma_alterada(bd_temporal):
    token_invalido = "JHT999|1|firma-falsa"
    valido, msg = validar_token(token_invalido)
    assert valido is False
    assert "firma" in msg.lower()


def test_escanear_marca_como_usada_la_reserva_vigente(reloj_fijo, bd_temporal):
    ruta = generar_qr("Pablo", "JHT999", "profesor")
    reloj_fijo(_dt.datetime(2026, 1, 1, 10, 5))
    res.crear_reserva("JHT999", "Zona A", "2026-01-01", "10:00", "11:00")

    resultado = escanear(ruta, zona="Zona A")
    assert resultado["valido"] is True
    assert resultado["tipo"] == "entrada"
    assert resultado["reserva"] is not None

    estados = [r["estado"] for r in get_conn().execute("SELECT estado FROM reservas")]
    assert estados == ["usada"]