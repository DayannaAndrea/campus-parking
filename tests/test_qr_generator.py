import os

from app.db import get_conn
from app.qr_generator import generar_qr


def test_generar_qr_crea_usuario_y_archivo(bd_temporal):
    ruta = generar_qr("Ana", "ABC123", "estudiante")
    assert os.path.exists(ruta)
    fila = get_conn().execute("SELECT * FROM usuarios WHERE placa = 'ABC123'").fetchone()
    assert fila
    assert fila["token"].startswith("ABC123|")


def test_placa_duplicada_regenera_el_qr(bd_temporal):
    ruta1 = generar_qr("Ana", "ABC123", "estudiante")
    ruta2 = generar_qr("Ana", "ABC123", "profesor")
    assert ruta1 == ruta2
    assert os.path.exists(ruta2)
    n = get_conn().execute("SELECT COUNT(*) AS n FROM usuarios WHERE placa = 'ABC123'").fetchone()["n"]
    assert n == 1