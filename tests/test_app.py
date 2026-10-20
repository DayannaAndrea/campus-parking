import json

from flask_app import app

from app import contingency as cont
from app.db import get_conn
from app.qr_generator import generar_qr


def test_home_200(cliente):
    resp = cliente.get("/")
    assert resp.status_code == 200
    assert "Campus Parking" in resp.get_data(as_text=True)


def test_panel_y_api_de_cupos(cliente, bd_temporal, como):
    como(cliente, "porteria")
    assert cliente.get("/panel").status_code == 200
    resp = cliente.get("/api/cupos")
    assert resp.status_code == 200
    datos = resp.get_json()
    assert len(datos) == 3  # zonas semilla
    assert {"zona", "ocupados", "disponibles", "alerta_llena"} <= set(datos[0])


def test_registro_crea_qr_y_redirige(cliente, bd_temporal):
    resp = cliente.post(
        "/registro",
        data={"nombre": "Ana", "placa": "abc123", "rol": "estudiante", "email": "ana@campus.edu",
              "password": "clave-segura", "password2": "clave-segura"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "ABC123" in body
    assert get_conn().execute("SELECT 1 FROM usuarios WHERE placa = 'ABC123'").fetchone()


def test_registro_duplicado_no_reescribe_la_placa(cliente, bd_temporal):
    # Antes, registrar de nuevo una placa reescribía sus datos (incluido el correo):
    # cualquiera podía quedarse con la cuenta ajena. Ahora se rechaza.
    datos = {"nombre": "Ana", "placa": "ABC123", "rol": "estudiante", "email": "ana@campus.edu",
             "password": "clave-segura", "password2": "clave-segura"}
    cliente.post("/registro", data=datos)
    cliente.get("/logout")  # el intruso no tiene la sesión de Ana
    resp = cliente.post(
        "/registro",
        data={**datos, "nombre": "Intruso", "email": "intruso@campus.edu", "rol": "profesor"},
        follow_redirects=True,
    )
    assert "ya está registrada" in resp.get_data(as_text=True)
    fila = get_conn().execute("SELECT nombre, email FROM usuarios WHERE placa = 'ABC123'").fetchone()
    assert (fila["nombre"], fila["email"]) == ("Ana", "ana@campus.edu")


def test_vigilante_valida_y_registra_entrada(cliente, bd_temporal, como):
    como(cliente, "porteria")
    generar_qr("Pablo", "JHT999", "profesor")
    resp = cliente.post(
        "/vigilante", data={"placa": "JHT999", "zona": "Zona A"}, follow_redirects=True)
    assert "VÁLIDO" in resp.get_data(as_text=True)
    assert get_conn().execute(
        "SELECT 1 FROM registros WHERE placa = 'JHT999' AND tipo = 'entrada'").fetchone()


def test_reservar_rechaza_placa_no_registrada(cliente, bd_temporal):
    # /reservar exige sesión y toma la placa de ella, no del formulario
    with cliente.session_transaction() as sess:
        sess["user_email"] = "fantasma@campus.edu"
        sess["user_name"] = "Fantasma"
        sess["user_placa"] = "ZZZ999"
        sess["rol"] = "conductor"
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