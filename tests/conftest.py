import datetime as _dt
import os

import pytest

os.environ["CSRF_OFF"] = "1"  # los tests envían POST sin token CSRF

import app.db as db
import app.qr_generator as qg
import app.contingency as cont


@pytest.fixture()
def bd_temporal(tmp_path, monkeypatch):
    """Aísla cada prueba en una BD SQLite propia (esquema + 3 zonas semilla)."""
    monkeypatch.setattr(db, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "campus_parking.db"))
    monkeypatch.setattr(qg, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(cont, "CACHE_PATH", str(tmp_path / "cache_placas.json"))
    monkeypatch.setattr(cont, "COLA_PATH", str(tmp_path / "cola_sincronizacion.json"))
    os.makedirs(os.path.join(str(tmp_path), "qrcodes"), exist_ok=True)
    db.init_db()
    yield db


@pytest.fixture()
def reloj_fijo(monkeypatch):
    """Congela datetime.now() dentro de app.reservations (para franjas/no-shot)."""
    import app.reservations as res

    real = _dt.datetime

    def aplicar(momento: _dt.datetime):
        class _Reloj(real):
            @classmethod
            def now(cls):
                return momento

        monkeypatch.setattr(res, "datetime", _Reloj)

    return aplicar


@pytest.fixture()
def cliente(bd_temporal, monkeypatch):
    import flask_app

    # La app usa DATA_DIR como global propio: apúntalo a la BD temporal.
    monkeypatch.setattr(flask_app, "DATA_DIR", db.DATA_DIR)
    return flask_app.app.test_client()


def iniciar_sesion(cliente, rol, placa=None):
    """Deja al cliente de pruebas con una sesión del rol indicado ('conductor', 'porteria', 'admin')."""
    with cliente.session_transaction() as sess:
        sess["rol"] = rol
        sess["user_name"] = rol
        if placa:
            sess["user_placa"] = placa
            sess["user_email"] = f"{placa.lower()}@campus.edu"
    return cliente


@pytest.fixture()
def como():
    return iniciar_sesion