"""Pruebas de autenticación y permisos por rol (conductor, portería, administración)."""
import pytest

from app import auth, reservations
from app.db import get_conn
from app.qr_generator import generar_qr

RUTAS_PORTERIA = ["/vigilante", "/contingencia", "/panel", "/reporte-seguridad"]
RUTAS_ADMIN = ["/usuarios", "/zonas", "/metricas", "/historial", "/historial/csv",
               "/medicion", "/medicion/csv", "/api/medicion", "/scheduler-status", "/sistema"]
CLAVE = "clave-segura"


def _registrar(cliente, placa="ABC123", email="ana@campus.edu", nombre="Ana"):
    return cliente.post("/registro", data={"nombre": nombre, "placa": placa, "rol": "estudiante",
                                           "email": email, "password": CLAVE, "password2": CLAVE})


# ---------- sin sesión ----------
@pytest.mark.parametrize("ruta", RUTAS_PORTERIA + RUTAS_ADMIN)
def test_sin_sesion_no_se_entra_al_personal(cliente, bd_temporal, ruta):
    r = cliente.get(ruta)
    assert r.status_code == 302 and "/login" in r.headers["Location"]


@pytest.mark.parametrize("ruta", ["/dashboard", "/reservar", "/mi-qr/ABC123", "/mis-reservas/ABC123"])
def test_sin_sesion_el_conductor_va_al_login(cliente, bd_temporal, ruta):
    r = cliente.get(ruta)
    assert r.status_code == 302 and "/login" in r.headers["Location"]


@pytest.mark.parametrize("ruta", ["/", "/login", "/registro", "/disponibilidad", "/api/cupos"])
def test_paginas_publicas(cliente, bd_temporal, ruta):
    assert cliente.get(ruta).status_code == 200


# ---------- por rol ----------
@pytest.mark.parametrize("ruta", RUTAS_PORTERIA + RUTAS_ADMIN)
def test_conductor_no_entra_a_porteria_ni_administracion(cliente, bd_temporal, como, ruta):
    como(cliente, "conductor", placa="ABC123")
    assert cliente.get(ruta).status_code == 403


def test_porteria_solo_ve_lo_suyo(cliente, bd_temporal, como):
    como(cliente, "porteria")
    for ruta in RUTAS_PORTERIA:
        assert cliente.get(ruta).status_code == 200, ruta
    for ruta in RUTAS_ADMIN + ["/dashboard", "/reservar"]:
        assert cliente.get(ruta).status_code == 403, ruta


def test_admin_entra_a_todo_lo_del_personal(cliente, bd_temporal, como):
    como(cliente, "admin")
    for ruta in RUTAS_PORTERIA + RUTAS_ADMIN:
        assert cliente.get(ruta).status_code == 200, ruta


def test_acciones_de_admin_bloqueadas_para_conductor(cliente, bd_temporal, como):
    generar_qr("Ana", "ABC123", "estudiante")
    como(cliente, "conductor", placa="ABC123")
    assert cliente.post("/vehiculos/ABC123/estado", data={"activo": "0"}).status_code == 403
    assert cliente.post("/zonas", data={"nombre": "Pirata", "aforo": "99"}).status_code == 403
    assert get_conn().execute("SELECT activo FROM usuarios WHERE placa='ABC123'").fetchone()["activo"] == 1


def test_cada_rol_llega_a_su_pantalla_con_su_menu(cliente, bd_temporal, como):
    html = cliente.get("/").get_data(as_text=True)  # visitante: portada pública
    assert "Iniciar sesión" in html and "Validar ingreso" not in html and "Mi panel" not in html
    generar_qr("Ana", "ABC123", "estudiante")
    como(cliente, "conductor", placa="ABC123")
    r = cliente.get("/")
    assert r.headers["Location"].endswith("/dashboard")
    html = cliente.get("/dashboard").get_data(as_text=True)
    assert "Mi panel" in html and "Validar ingreso" not in html and "Resumen" not in html
    como(cliente, "porteria")
    assert cliente.get("/").headers["Location"].endswith("/vigilante")
    html = cliente.get("/vigilante").get_data(as_text=True)
    assert "Validar ingreso" in html and "Zonas y aforo" not in html and "Mi panel" not in html
    como(cliente, "admin")
    assert cliente.get("/").headers["Location"].endswith("/resumen")
    html = cliente.get("/resumen").get_data(as_text=True)
    assert "Zonas y aforo" in html and "Validar ingreso" in html and "vehículos dentro" in html


# ---------- datos de otro conductor ----------
def test_conductor_solo_ve_su_qr_y_sus_reservas(cliente, bd_temporal, como):
    generar_qr("Ana", "ABC123", "estudiante")
    generar_qr("Beto", "XYZ789", "estudiante")
    como(cliente, "conductor", placa="ABC123")
    assert cliente.get("/mi-qr/ABC123").status_code == 200
    assert cliente.get("/qr-imagen/ABC123").status_code == 200
    assert cliente.get("/mis-reservas/ABC123").status_code == 200
    for ruta in ("/mi-qr/XYZ789", "/qr-imagen/XYZ789", "/mis-reservas/XYZ789"):
        assert cliente.get(ruta).status_code == 403, ruta


def test_no_se_cancela_la_reserva_de_otro(cliente, bd_temporal, como):
    generar_qr("Beto", "XYZ789", "estudiante")
    reservations.crear_reserva("XYZ789", "Zona A", "2099-01-01", "08:00", "09:00", enviar_confirmacion=False)
    rid = get_conn().execute("SELECT id FROM reservas").fetchone()["id"]
    como(cliente, "conductor", placa="ABC123")
    assert cliente.post(f"/reservas/{rid}/cancelar").status_code == 403
    assert get_conn().execute("SELECT estado FROM reservas WHERE id=?", (rid,)).fetchone()["estado"] != "cancelada"


# ---------- login de conductores ----------
def test_registro_guarda_la_clave_cifrada_e_inicia_sesion(cliente, bd_temporal):
    r = _registrar(cliente)
    assert r.status_code == 302 and "/mi-qr/ABC123" in r.headers["Location"]
    guardada = get_conn().execute("SELECT password_hash FROM usuarios WHERE placa='ABC123'").fetchone()[0]
    assert guardada and CLAVE not in guardada
    assert cliente.get("/dashboard").status_code == 200


@pytest.mark.parametrize("cambios, mensaje", [
    ({"password": "corta", "password2": "corta"}, "al menos 8"),
    ({"password2": "otra-distinta"}, "no coinciden"),
    ({"email": ""}, "correo es obligatorio"),
])
def test_registro_valida_correo_y_clave(cliente, bd_temporal, cambios, mensaje):
    datos = {"nombre": "Ana", "placa": "ABC123", "rol": "estudiante", "email": "ana@campus.edu",
             "password": CLAVE, "password2": CLAVE, **cambios}
    r = cliente.post("/registro", data=datos)
    assert r.status_code == 200 and mensaje in r.get_data(as_text=True)
    assert get_conn().execute("SELECT 1 FROM usuarios WHERE placa='ABC123'").fetchone() is None


def test_login_exige_la_clave_correcta(cliente, bd_temporal):
    _registrar(cliente)
    cliente.get("/logout")
    r = cliente.post("/login", data={"email": "ana@campus.edu", "password": "incorrecta"})
    assert "incorrectos" in r.get_data(as_text=True)
    assert cliente.get("/dashboard").status_code == 302
    r = cliente.post("/login", data={"email": "ANA@campus.edu", "password": CLAVE})
    assert r.status_code == 302 and cliente.get("/dashboard").status_code == 200


def test_login_solo_con_correo_ya_no_basta(cliente, bd_temporal):
    _registrar(cliente)
    cliente.get("/logout")
    cliente.post("/login", data={"email": "ana@campus.edu"})
    assert cliente.get("/dashboard").status_code == 302


def test_login_no_redirige_a_otros_sitios(cliente, bd_temporal):
    _registrar(cliente)
    cliente.get("/logout")
    r = cliente.post("/login?next=//sitio-malo.com", data={"email": "ana@campus.edu", "password": CLAVE})
    assert r.headers["Location"].endswith("/dashboard")
    cliente.get("/logout")
    r = cliente.post("/login?next=/reservar", data={"email": "ana@campus.edu", "password": CLAVE})
    assert r.headers["Location"].endswith("/reservar")


def test_registro_antiguo_sin_clave_la_crea_solo_con_su_mismo_correo(cliente, bd_temporal):
    generar_qr("Ana", "ABC123", "estudiante", email="ana@campus.edu")  # registro previo, sin contraseña
    r = cliente.post("/login", data={"email": "ana@campus.edu", "password": CLAVE}, follow_redirects=True)
    assert "vuelve a registrar" in r.get_data(as_text=True)
    assert "ya está registrada" in _registrar(cliente, email="otro@campus.edu", nombre="Intruso").get_data(as_text=True)
    assert _registrar(cliente).status_code == 302
    assert auth.verificar_conductor("ana@campus.edu", CLAVE) is not None


# ---------- ingreso del personal ----------
def test_personal_entra_con_la_clave_del_env(cliente, bd_temporal, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "admin-secreta")
    monkeypatch.setenv("PORTERIA_PASSWORD", "porteria-secreta")
    r = cliente.post("/login", data={"usuario": "admin", "password": "porteria-secreta"})
    assert "incorrectos" in r.get_data(as_text=True)
    cliente.post("/login", data={"usuario": "porteria", "password": "porteria-secreta"})
    assert cliente.get("/vigilante").status_code == 200 and cliente.get("/usuarios").status_code == 403
    cliente.get("/logout")
    cliente.post("/login", data={"usuario": "admin", "password": "admin-secreta"})
    assert cliente.get("/usuarios").status_code == 200


def test_cuenta_de_personal_sin_clave_en_env_queda_deshabilitada(cliente, bd_temporal, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "")
    cliente.post("/login", data={"usuario": "admin", "password": ""})
    assert cliente.get("/usuarios").status_code == 302
    assert not auth.verificar_personal("root", "lo-que-sea")


# ---------- flujo de cada rol ----------
def test_conductor_con_sesion_no_ve_login_ni_registro(cliente, bd_temporal):
    _registrar(cliente)
    assert cliente.get("/login").headers["Location"].endswith("/dashboard")
    assert cliente.get("/registro").headers["Location"].endswith("/dashboard")


def test_porteria_no_registra_vehiculos(cliente, bd_temporal, como):
    como(cliente, "porteria")
    assert cliente.get("/registro").status_code == 403


def test_admin_registra_a_nombre_de_otro_sin_perder_su_sesion(cliente, bd_temporal, como):
    como(cliente, "admin")
    r = _registrar(cliente)
    assert r.status_code == 302 and "/mi-qr/ABC123" in r.headers["Location"]
    with cliente.session_transaction() as sess:
        assert sess["rol"] == "admin"
    assert cliente.get("/usuarios").status_code == 200


def test_el_next_no_lleva_signo_de_interrogacion_suelto(cliente, bd_temporal):
    assert cliente.get("/dashboard").headers["Location"].endswith("next=/dashboard")


def test_login_unico_lleva_al_personal_a_su_pantalla(cliente, bd_temporal, monkeypatch):
    monkeypatch.setenv("PORTERIA_PASSWORD", "porteria-secreta")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin-secreta")
    r = cliente.post("/login", data={"usuario": "Porteria", "password": "porteria-secreta"})
    assert r.headers["Location"].endswith("/vigilante")
    cliente.get("/logout")
    r = cliente.post("/login", data={"usuario": "admin", "password": "admin-secreta"})
    assert r.headers["Location"].endswith("/resumen")


def test_la_direccion_antigua_del_personal_lleva_al_login(cliente, bd_temporal):
    assert "/login" in cliente.get("/personal").headers["Location"]


def test_resumen_del_admin_muestra_indicadores(cliente, bd_temporal, como):
    from app.validator import escanear
    ruta = generar_qr("Ana", "ABC123", "estudiante")
    escanear(ruta, zona="Zona A")
    como(cliente, "admin")
    html = cliente.get("/resumen").get_data(as_text=True)
    assert "vehículos dentro" in html and "ABC123" in html and "Entrada" in html


@pytest.mark.parametrize("ruta, codigo, texto", [
    ("/no-existe", 404, "Página no encontrada"),
    ("/usuarios", 403, "Acceso denegado"),
])
def test_paginas_de_error_con_diseno(cliente, bd_temporal, como, ruta, codigo, texto):
    como(cliente, "conductor", placa="ABC123")
    r = cliente.get(ruta)
    html = r.get_data(as_text=True)
    assert r.status_code == codigo and texto in html and "Campus Parking" in html


def test_csrf_invalido_muestra_pagina_propia(bd_temporal, monkeypatch):
    import flask_app
    monkeypatch.setitem(flask_app.app.config, "CSRF_OFF", False)
    r = flask_app.app.test_client().post("/login", data={"email": "a@b.co", "password": "x"})
    assert r.status_code == 400 and "Solicitud no válida" in r.get_data(as_text=True)


def test_reserva_no_promete_correo_si_no_esta_configurado(cliente, bd_temporal, como, monkeypatch):
    from app.email_service import EmailConfig
    monkeypatch.setattr(EmailConfig, "is_configured", classmethod(lambda cls: False))
    generar_qr("Ana", "ABC123", "estudiante")
    como(cliente, "conductor", placa="ABC123")
    html = cliente.get("/reservar").get_data(as_text=True)
    assert "correo de confirmación" not in html
    r = cliente.post("/reservar", data={"zona": "Zona A", "fecha": "2099-01-01", "hora_inicio": "08:00",
                                        "hora_fin": "09:00"}, follow_redirects=True)
    assert "Reserva creada" in r.get_data(as_text=True) and "Revisa tu correo" not in r.get_data(as_text=True)
