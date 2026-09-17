import json

from flask_app import app

from app import contingency as cont
from app.db import get_conn
from app.qr_generator import generar_qr


def test_home_200(cliente):
    resp = cliente.get("/")
    assert resp.status_code == 200
    assert "Campus Parking" in resp.get_data(as_text=True)


def test_panel_y_api_de_cupos(cliente, bd_temporal):
    assert cliente.get("/panel").status_code == 200
    resp = cliente.get("/api/cupos")
    assert resp.status_code == 200
    datos = resp.get_json()
    assert len(datos) == 3  # zonas semilla
    assert {"zona", "ocupados", "disponibles", "alerta_llena"} <= set(datos[0])


def test_registro_crea_qr_y_redirige(cliente, bd_temporal):
    resp = cliente.post(
        "/registro",
        data={"nombre": "Ana", "placa": "abc123", "rol": "estudiante"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "ABC123" in body
    assert get_conn().execute("SELECT 1 FROM usuarios WHERE placa = 'ABC123'").fetchone()


def test_registro_duplicado_regenere_qr(cliente, bd_temporal):
    cliente.post("/registro", data={"nombre": "Ana", "placa": "ABC123", "rol": "estudiante"})
    resp = cliente.post(
        "/registro",
        data={"nombre": "Ana", "placa": "ABC123", "rol": "profesor"},
        follow_redirects=True,
    )
    assert "QR regenerado" in resp.get_data(as_text=True)


def test_vigilante_valida_y_registra_entrada(cliente, bd_temporal):
    generar_qr("Pablo", "JHT999", "profesor")
    resp = cliente.post(
        "/vigilante", data={"placa": "JHT999", "zona": "Zona A"}, follow_redirects=True)
    assert "VÁLIDO" in resp.get_data(as_text=True)
    assert get_conn().execute(
        "SELECT 1 FROM registros WHERE placa = 'JHT999' AND tipo = 'entrada'").fetchone()


def test_reservar_rechaza_placa_no_registrada(cliente, bd_temporal):
    resp = cliente.post(
        "/reservar",
        data={"placa": "ZZZ999", "zona": "Zona A", "fecha": "2026-01-01",
              "hora_inicio": "10:00", "hora_fin": "11:00"},
        follow_redirects=True,
    )
    assert "no está registrada" in resp.get_data(as_text=True)


def test_before_request_vacia_la_cola_de_contingencia(cliente, bd_temporal):
    with open(cont.COLA_PATH, "w") as f:
        json.dump([{"placa": "DEF456", "tipo": "entrada", "metodo": "contingencia",
                    "timestamp": "2026-01-01T12:00:00"}], f)
    cliente.get("/")  # cualquier request dispara before_request
    assert get_conn().execute(
        "SELECT 1 FROM registros WHERE placa = 'DEF456' AND metodo = 'contingencia'").fetchone()