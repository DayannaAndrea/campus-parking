"""
Capa de datos compartida por todos los módulos del Sprint 1.
Historia relacionada: base de todas (M1-01 a M1-04).
"""
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "campus_parking.db")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "qrcodes"), exist_ok=True)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            placa TEXT UNIQUE NOT NULL,
            rol TEXT NOT NULL CHECK(rol IN ('estudiante','profesor','administrativo')),
            token TEXT NOT NULL,
            activo INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('entrada','salida')),
            metodo TEXT NOT NULL CHECK(metodo IN ('qr','contingencia')),
            zona TEXT,
            timestamp TEXT NOT NULL
        )
        """
    )
    # Sprint 2 — M2-01: zonas y aforo
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS zonas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            aforo_maximo INTEGER NOT NULL
        )
        """
    )
    # Sprint 3 — M3-01/M3-02: reservas por franja horaria
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT NOT NULL,
            zona TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora_inicio TEXT NOT NULL,
            hora_fin TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'activa'
                CHECK(estado IN ('activa','usada','liberada','cancelada')),
            creada TEXT NOT NULL
        )
        """
    )
    # Sprint 3 — M3-06: agregar columna para tracking de recordatorios
    try:
        conn.execute("ALTER TABLE reservas ADD COLUMN recordatorio_enviado INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # La columna ya existe
    conn.commit()

    # Semilla de zonas si la tabla está vacía (para que el panel no arranque en cero)
    cur = conn.execute("SELECT COUNT(*) AS n FROM zonas").fetchone()
    if cur["n"] == 0:
        for nombre, aforo in [("Zona A", 100), ("Zona B", 100), ("Zona C", 100)]:
            conn.execute("INSERT INTO zonas (nombre, aforo_maximo) VALUES (?, ?)", (nombre, aforo))
        conn.commit()
    conn.close()


def ultimo_tipo_registro(placa: str):
    """Devuelve 'entrada' o 'salida' (el último registrado) o None si nunca ha entrado."""
    conn = get_conn()
    row = conn.execute(
        "SELECT tipo FROM registros WHERE placa = ? ORDER BY id DESC LIMIT 1",
        (placa,),
    ).fetchone()
    conn.close()
    return row["tipo"] if row else None


init_db()
