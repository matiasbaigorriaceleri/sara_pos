"""
SARA POS — Migración automática de base de datos
=================================================
Se ejecuta al arrancar la app, ANTES de crear tablas con
Base.metadata.create_all(). Agrega columnas faltantes en tablas
existentes para que bases de datos viejas funcionen con el código
nuevo, sin perder ningún dato.

Esto resuelve el problema de clientes que tenían una instalación
anterior (con estructura vieja de tickets sin status/cancel_reason/
cancelled_by/cancelled_at) y al actualizar la app obtenían:
  sqlite3.OperationalError: table tickets has no column named status
"""

import sqlite3
import os
import sys


def _get_db_path() -> str:
    if getattr(sys, 'frozen', False):
        if sys.platform == "win32":
            base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "SARA_POS")
        elif sys.platform == "darwin":
            base = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "SARA_POS")
        else:
            base = os.path.join(os.path.expanduser("~"), ".sara_pos")
        os.makedirs(base, exist_ok=True)
    else:
        base = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
    return os.path.join(base, "database.db")


def _get_existing_columns(cursor, table_name: str) -> set:
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def run_migrations():
    """
    Aplica migraciones necesarias sobre la base de datos existente.
    Es idempotente: puede correrse múltiples veces sin efectos secundarios.
    Si la base no existe todavía, no hace nada (create_all la creará después).
    """
    db_path = _get_db_path()

    if not os.path.exists(db_path):
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # ── Tabla: tickets ────────────────────────────────────────────────
        # Columnas agregadas en el módulo de anulación de ventas.
        # Bases anteriores a esa versión no las tienen.
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tickets'")
        if cursor.fetchone():
            existing = _get_existing_columns(cursor, "tickets")

            migrations = [
                ("status",       "ALTER TABLE tickets ADD COLUMN status TEXT DEFAULT 'active'"),
                ("cancel_reason","ALTER TABLE tickets ADD COLUMN cancel_reason TEXT DEFAULT ''"),
                ("cancelled_by", "ALTER TABLE tickets ADD COLUMN cancelled_by TEXT DEFAULT ''"),
                ("cancelled_at", "ALTER TABLE tickets ADD COLUMN cancelled_at DATETIME"),
            ]

            for col_name, sql in migrations:
                if col_name not in existing:
                    cursor.execute(sql)

        conn.commit()
        conn.close()

    except Exception:
        # Silencioso: si algo falla acá, la app sigue arrancando normal
        # y el error real aparecerá después al intentar usar la DB.
        try:
            conn.close()
        except Exception:
            pass