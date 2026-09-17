import datetime as _dt

import pytest

from app import reservations as res
from app.db import get_conn
from app.qr_generator import generar_qr


def _registrar(placa="ABC123", rol="estudiante"):
    generar_qr("Ana", placa, rol)
    return placa


def test_rechaza_placa_no_registrada(bd_temporal):
    with pytest.raises(ValueError):
        res.crear_reserva("ZZZ999", "Zona A", "2026-01-01", "10:00", "11:00")


def test_rechaza_hora_de_fin_menor_o_igual(bd_temporal):
    _registrar()
    with pytest.raises(ValueError):
        res.crear_reserva("ABC123", "Zona A", "2026-01-01", "11:00", "10:00")
    with pytest.raises(ValueError):
        res.crear_reserva("ABC123", "Zona A", "2026-01-01", "10:00", "10:00")


def test_rechaza_zona_inexistente(bd_temporal):
    _registrar()
    with pytest.raises(ValueError):
        res.crear_reserva("ABC123", "Zona Z", "2026-01-01", "10:00", "11:00")


def test_rechaza_formato_invalido(bd_temporal):
    _registrar()
    with pytest.raises(ValueError):
        res.crear_reserva("ABC123", "Zona A", "01/01/2026", "10:00", "11:00")


def test_rechaza_solapamiento_de_franja_misma_placa(bd_temporal):
    _registrar()
    res.crear_reserva("ABC123", "Zona A", "2026-01-01", "10:00", "11:00")
    with pytest.raises(ValueError):
        res.crear_reserva("ABC123", "Zona A", "2026-01-01", "10:30", "11:30")


def test_respeta_el_aforo_de_la_zona(bd_temporal):
    _registrar("ABC123")
    _registrar("DEF456")
    _registrar("GHI789")
    conn = get_conn()
    conn.execute("INSERT INTO zonas (nombre, aforo_maximo) VALUES ('Zona Mini', 2)")
    conn.commit()
    conn.close()

    res.crear_reserva("ABC123", "Zona Mini", "2026-01-01", "10:00", "11:00")
    res.crear_reserva("DEF456", "Zona Mini", "2026-01-01", "10:00", "11:00")
    with pytest.raises(ValueError):
        res.crear_reserva("GHI789", "Zona Mini", "2026-01-01", "10:00", "11:00")


def test_marcar_reserva_usada_solo_la_vigente(bd_temporal):
    _registrar()
    res.crear_reserva("ABC123", "Zona A", "2026-01-01", "10:00", "11:00")
    res.crear_reserva("ABC123", "Zona A", "2026-01-01", "14:00", "15:00")
    ids = [r["id"] for r in get_conn().execute("SELECT id FROM reservas ORDER BY id")]
    res.marcar_reserva_usada("ABC123", ids[0])
    estados = [r["estado"] for r in get_conn().execute("SELECT estado FROM reservas ORDER BY id")]
    assert estados == ["usada", "activa"]


def test_reserva_vigente_y_liberacion_por_no_show(reloj_fijo, bd_temporal):
    _registrar()
    reloj_fijo(_dt.datetime(2026, 1, 1, 10, 5))

    res.crear_reserva("ABC123", "Zona A", "2026-01-01", "10:00", "11:00")
    res.crear_reserva("ABC123", "Zona A", "2026-01-01", "09:00", "09:45")  # sin llegada -> no-show

    vigente = res.reserva_vigente("ABC123")
    assert vigente["hora_inicio"] == "10:00"
    assert res.liberar_no_shows() == 0  # la no-show ya fue liberada por reserva_vigente
    estados = [r["estado"] for r in get_conn().execute(
        "SELECT estado FROM reservas WHERE hora_inicio = '09:00'")]
    assert estados == ["liberada"]


def test_historial_csv_y_reporte_sin_reserva(bd_temporal):
    _registrar("ABC123")
    _registrar("DEF456")
    hoy = _dt.date.today().isoformat()
    # franja que cubre cualquier hora de hoy, para que ABC123 siempre "tenga reserva"
    res.crear_reserva("ABC123", "Zona A", hoy, "00:00", "23:59")
    from app.entry_log import registrar_evento
    registrar_evento("ABC123", "qr", "Zona A")  # entrada con reserva vigente
    registrar_evento("DEF456", "qr", "Zona B")  # sin reserva -> debe aparecer
    csv_texto = res.historial_csv()
    assert "placa,tipo,metodo,zona,timestamp" in csv_texto
    assert "DEF456" in csv_texto
    reporte = res.reporte_sin_reserva(hoy)
    assert [r["placa"] for r in reporte] == ["DEF456"]