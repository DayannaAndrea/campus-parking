"""Pruebas de las funciones de cierre: cancelar reserva, baja de vehículos y medición de aceptación."""
from datetime import date, timedelta

import pytest

from app import aceptacion, reservations
from app.db import get_conn
from app.entry_log import cambiar_estado_usuario
from app.qr_generator import generar_qr
from app.validator import escanear


# ---------- cancelar reservas ----------
def _reserva(placa="ABC123"):
    generar_qr("Ana", placa, "estudiante")
    reservations.crear_reserva(placa, "Zona A", "2099-01-01", "08:00", "09:00")
    return get_conn().execute("SELECT id FROM reservas ORDER BY id DESC").fetchone()["id"]


def test_cancelar_reserva_activa(bd_temporal):
    rid = _reserva()
    assert reservations.cancelar_reserva(rid) == "ABC123"
    assert get_conn().execute("SELECT estado FROM reservas WHERE id=?", (rid,)).fetchone()["estado"] == "cancelada"


def test_no_se_cancela_dos_veces_ni_una_inexistente(bd_temporal):
    rid = _reserva()
    reservations.cancelar_reserva(rid)
    with pytest.raises(ValueError):
        reservations.cancelar_reserva(rid)
    with pytest.raises(ValueError):
        reservations.cancelar_reserva(9999)


def test_cancelar_libera_el_cupo_de_la_franja(bd_temporal):
    c = get_conn()
    c.execute("INSERT INTO zonas (nombre, aforo_maximo) VALUES ('Mini', 1)")
    c.commit()
    generar_qr("A", "AAA111", "estudiante")
    generar_qr("B", "BBB222", "estudiante")
    reservations.crear_reserva("AAA111", "Mini", "2099-01-01", "08:00", "09:00")
    with pytest.raises(ValueError):
        reservations.crear_reserva("BBB222", "Mini", "2099-01-01", "08:00", "09:00")
    rid = get_conn().execute("SELECT id FROM reservas").fetchone()["id"]
    reservations.cancelar_reserva(rid)
    reservations.crear_reserva("BBB222", "Mini", "2099-01-01", "08:00", "09:00")  # ya hay cupo


def test_ruta_cancelar_reserva(cliente, bd_temporal, como):
    rid = _reserva()
    como(cliente, "conductor", placa="ABC123")  # el dueño de la reserva
    r = cliente.post(f"/reservas/{rid}/cancelar", follow_redirects=True)
    assert r.status_code == 200 and "Reserva cancelada" in r.get_data(as_text=True)


# ---------- baja / reactivar ----------
def test_baja_impide_el_ingreso_y_reactivar_lo_permite(bd_temporal):
    ruta = generar_qr("Ana", "ABC123", "estudiante")
    cambiar_estado_usuario("ABC123", False)
    assert escanear(ruta)["valido"] is False
    cambiar_estado_usuario("ABC123", True)
    assert escanear(ruta)["valido"] is True


def test_no_se_da_de_baja_a_un_vehiculo_que_esta_dentro(bd_temporal):
    ruta = generar_qr("Ana", "ABC123", "estudiante")
    escanear(ruta, zona="Zona A")
    with pytest.raises(ValueError, match="dentro"):
        cambiar_estado_usuario("ABC123", False)


def test_baja_de_placa_inexistente(bd_temporal):
    with pytest.raises(ValueError):
        cambiar_estado_usuario("ZZZ999", False)


def test_ruta_baja_actualiza_cache_de_contingencia(cliente, bd_temporal, como):
    from app import contingency as cont
    como(cliente, "admin")
    generar_qr("Ana", "ABC123", "estudiante")
    cliente.post("/vehiculos/ABC123/estado", data={"activo": "0"})
    assert cont.validar_manual("ABC123") is False


# ---------- medición de aceptación ----------
def _dia(fecha, n=20, minutos=2.5):
    for _ in range(n):
        aceptacion.registrar_medicion(minutos * 60, fecha=fecha)


def _habiles(inicio, n):
    d, out = inicio, []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


LUNES = date(2026, 10, 12)


def test_cinco_dias_habiles_que_cumplen_aprueban(bd_temporal):
    for f in _habiles(LUNES, 5):
        _dia(f)
    r = aceptacion.evaluar()
    assert r["aprobado"] and r["racha"] == 5


def test_cuatro_dias_no_alcanzan(bd_temporal):
    for f in _habiles(LUNES, 4):
        _dia(f)
    assert not aceptacion.evaluar()["aprobado"]


def test_un_dia_sobre_la_meta_reinicia_la_racha(bd_temporal):
    fechas = _habiles(LUNES, 6)
    for i, f in enumerate(fechas):
        _dia(f, minutos=3.4 if i == 2 else 2.5)
    r = aceptacion.evaluar()
    assert not r["aprobado"] and r["racha"] == 3


def test_dia_con_pocos_vehiculos_no_cuenta(bd_temporal):
    for i, f in enumerate(_habiles(LUNES, 5)):
        _dia(f, n=19 if i == 0 else 20)
    r = aceptacion.evaluar()
    assert not r["aprobado"] and r["dias"][0]["motivo"].startswith("faltan")


def test_el_fin_de_semana_no_rompe_la_racha(bd_temporal):
    # lunes a viernes de una semana cuentan seguidos, y el lunes siguiente continúa
    for f in _habiles(date(2026, 10, 14), 5):  # miércoles a martes (salta sábado y domingo)
        _dia(f)
    assert aceptacion.evaluar()["aprobado"]


def test_un_hueco_de_un_dia_habil_rompe_la_racha(bd_temporal):
    fechas = _habiles(LUNES, 6)
    del fechas[2]
    for f in fechas:
        _dia(f)
    assert aceptacion.evaluar()["racha"] == 3


@pytest.mark.parametrize("valor", [0, -5, "abc", 99999, None])
def test_mediciones_invalidas_se_rechazan(bd_temporal, valor):
    with pytest.raises(ValueError):
        aceptacion.registrar_medicion(valor)


def test_deshacer_borra_la_ultima(bd_temporal):
    aceptacion.registrar_medicion(60)
    aceptacion.registrar_medicion(90)
    assert aceptacion.borrar_ultima_medicion()
    assert aceptacion.evaluar()["total_mediciones"] == 1


def test_pantalla_y_registro_de_medicion(cliente, bd_temporal, como):
    como(cliente, "admin")
    assert cliente.get("/medicion").status_code == 200
    r = cliente.post("/medicion", data={"minutos": "2,5", "placa": "abc123"}, follow_redirects=True)
    assert "Medición registrada" in r.get_data(as_text=True)
    assert cliente.get("/api/medicion").get_json()["total_mediciones"] == 1
    assert "2,5" not in cliente.get("/medicion/csv").get_data(as_text=True)  # se guarda en segundos
    assert "150.0" in cliente.get("/medicion/csv").get_data(as_text=True)


def test_medicion_manual_invalida_muestra_error(cliente, bd_temporal, como):
    como(cliente, "admin")
    r = cliente.post("/medicion", data={"minutos": "0"}, follow_redirects=True)
    assert "entre 1 segundo y 60 minutos" in r.get_data(as_text=True)


def test_formularios_nuevos_llevan_token_csrf(bd_temporal, monkeypatch, como):
    """Con CSRF activo, los formularios de cancelar, baja y medición deben enviar el token."""
    import re
    import flask_app
    from app import qr_generator

    monkeypatch.setitem(flask_app.app.config, "CSRF_OFF", False)
    qr_generator.generar_qr("Prueba", "CSR123", "estudiante")
    c = como(flask_app.app.test_client(), "admin")
    for ruta in ("/medicion", "/usuarios"):
        html = c.get(ruta).get_data(as_text=True)
        assert html.count('name="csrf_token"') == html.count("<form"), ruta
    assert c.post("/medicion", data={"minutos": "2"}).status_code == 400  # sin token
    token = re.search(r'name="csrf_token" value="([0-9a-f]+)"', c.get("/medicion").get_data(as_text=True)).group(1)
    assert c.post("/medicion", data={"minutos": "2", "csrf_token": token}).status_code == 302
