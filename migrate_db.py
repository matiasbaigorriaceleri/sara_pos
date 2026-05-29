"""
SARA POS — Migración de base de datos
======================================
Importa datos de la base vieja (database_.db) a la nueva (database.db).
Preserva todos los datos existentes en la nueva base.
Evita duplicados por nombre/barcode en productos y por username en usuarios.

Uso:
    python migrate_db.py
"""

import sqlite3
import os
import shutil
from datetime import datetime


OLD_DB = "database_.db"
NEW_DB = "database.db"


def migrate():
    print("=" * 55)
    print("  SARA POS — Migración de base de datos")
    print("=" * 55)
    print()

    # Verificar archivos
    if not os.path.exists(OLD_DB):
        print(f"❌ No se encontró {OLD_DB}")
        return

    if not os.path.exists(NEW_DB):
        print(f"❌ No se encontró {NEW_DB}")
        return

    # Backup de seguridad de la base nueva
    backup_path = f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(NEW_DB, backup_path)
    print(f"✅ Backup creado: {backup_path}")
    print()

    old = sqlite3.connect(OLD_DB)
    new = sqlite3.connect(NEW_DB)
    old.row_factory = sqlite3.Row
    new.row_factory = sqlite3.Row

    try:
        _migrate_products(old, new)
        _migrate_clients(old, new)
        _migrate_suppliers(old, new)
        _migrate_supplier_invoices(old, new)
        _migrate_client_accounts(old, new)
        _migrate_settings(old, new)
        _migrate_users(old, new)

        new.commit()
        print()
        print("=" * 55)
        print("  ✅ Migración completada exitosamente")
        print("=" * 55)

    except Exception as e:
        new.rollback()
        print(f"\n❌ Error durante la migración: {e}")
        print(f"   La base de datos NO fue modificada.")
        import traceback
        traceback.print_exc()

    finally:
        old.close()
        new.close()


def _migrate_products(old, new):
    print("📦 Migrando productos...")

    old_products = old.execute("SELECT * FROM products WHERE is_active = 1").fetchall()

    # Obtener nombres y barcodes existentes en la nueva BD
    existing_names = set(
        r[0] for r in new.execute("SELECT name FROM products WHERE is_active = 1").fetchall()
    )
    existing_barcodes = set(
        r[0] for r in new.execute("SELECT barcode FROM products").fetchall()
    )

    # Obtener max code actual
    all_codes = new.execute("SELECT product_code FROM products").fetchall()
    max_code = 0
    for (code,) in all_codes:
        try:
            val = int(code)
            if val > max_code:
                max_code = val
        except Exception:
            pass

    imported = 0
    skipped = 0

    for p in old_products:
        name    = (p["name"] or "").strip().upper()
        barcode = (p["barcode"] or "").strip()

        if not name or not barcode:
            skipped += 1
            continue

        if name in existing_names or barcode in existing_barcodes:
            skipped += 1
            continue

        max_code += 1
        new.execute("""
            INSERT INTO products
                (product_code, name, detail, barcode, stock, minimum_stock,
                 price, cost_price, category, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            str(max_code).zfill(3),
            name,
            (p["detail"] or "").strip().upper(),
            barcode,
            p["stock"] or 0,
            p["minimum_stock"] or 0,
            p["price"] or 0,
            p["cost_price"] or 0,
            (p["category"] or "").strip().upper(),
        ))
        existing_names.add(name)
        existing_barcodes.add(barcode)
        imported += 1

    print(f"   Importados: {imported} | Omitidos (duplicados): {skipped}")


def _migrate_clients(old, new):
    print("👥 Migrando clientes...")

    old_clients = old.execute("SELECT * FROM clients WHERE is_active = 1").fetchall()

    existing_names = set(
        r[0] for r in new.execute("SELECT name FROM clients WHERE is_active = 1").fetchall()
    )

    # Obtener último número de cuenta
    last_accounts = new.execute("SELECT account_number FROM clients ORDER BY id DESC").fetchall()
    max_num = 0
    for (acc,) in last_accounts:
        try:
            num = int((acc or "").replace("CC-", ""))
            if num > max_num:
                max_num = num
        except Exception:
            pass

    imported = 0
    skipped = 0

    for c in old_clients:
        name = (c["name"] or "").strip().upper()
        if not name or name in existing_names:
            skipped += 1
            continue

        max_num += 1
        new.execute("""
            INSERT INTO clients
                (account_number, name, phone, email, address, notes, discount, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            f"CC-{str(max_num).zfill(5)}",
            name,
            c["phone"] or "",
            c["email"] or "",
            c["address"] or "",
            c["notes"] or "",
            c["discount"] or 0,
        ))
        existing_names.add(name)
        imported += 1

    print(f"   Importados: {imported} | Omitidos (duplicados): {skipped}")


def _migrate_suppliers(old, new):
    print("🏭 Migrando proveedores...")

    old_suppliers = old.execute("SELECT * FROM suppliers WHERE is_active = 1").fetchall()

    existing_names = set(
        r[0] for r in new.execute("SELECT name FROM suppliers WHERE is_active = 1").fetchall()
    )

    imported = 0
    skipped = 0

    for s in old_suppliers:
        name = (s["name"] or "").strip().upper()
        if not name or name in existing_names:
            skipped += 1
            continue

        new.execute("""
            INSERT INTO suppliers
                (name, contact, phone, email, address, notes, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (
            name,
            s["contact"] or "",
            s["phone"] or "",
            s["email"] or "",
            s["address"] or "",
            s["notes"] or "",
        ))
        existing_names.add(name)
        imported += 1

    print(f"   Importados: {imported} | Omitidos (duplicados): {skipped}")


def _migrate_supplier_invoices(old, new):
    print("📄 Migrando facturas de proveedores...")

    # Mapear nombres de proveedores viejos → IDs nuevos
    old_suppliers = {
        r["id"]: r["name"]
        for r in old.execute("SELECT id, name FROM suppliers").fetchall()
    }
    new_supplier_ids = {
        r[0]: r[1]
        for r in new.execute("SELECT name, id FROM suppliers").fetchall()
    }

    old_invoices = old.execute("SELECT * FROM supplier_invoices").fetchall()

    imported = 0
    skipped = 0

    for inv in old_invoices:
        old_sup_name = old_suppliers.get(inv["supplier_id"], "").upper()
        new_sup_id   = new_supplier_ids.get(old_sup_name)

        if not new_sup_id:
            skipped += 1
            continue

        new.execute("""
            INSERT INTO supplier_invoices
                (supplier_id, invoice_number, entry_date, payment_date,
                 amount, is_paid, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            new_sup_id,
            inv["invoice_number"] or "",
            inv["entry_date"],
            inv["payment_date"],
            inv["amount"] or 0,
            inv["is_paid"] or 0,
            inv["notes"] or "",
        ))
        imported += 1

    print(f"   Importados: {imported} | Omitidos (proveedor no encontrado): {skipped}")


def _migrate_client_accounts(old, new):
    print("💳 Migrando cuentas corrientes...")

    old_clients = {
        r["id"]: r["name"]
        for r in old.execute("SELECT id, name FROM clients").fetchall()
    }
    new_client_data = {
        r[0]: (r[1], r[2])
        for r in new.execute("SELECT name, id, account_number FROM clients").fetchall()
    }

    old_accounts = old.execute("SELECT * FROM client_accounts").fetchall()

    imported = 0
    skipped = 0

    for acc in old_accounts:
        old_cli_name = old_clients.get(acc["client_id"], "").upper()
        new_cli_info = new_client_data.get(old_cli_name)

        if not new_cli_info:
            skipped += 1
            continue

        new_cli_id, new_acc_num = new_cli_info

        new.execute("""
            INSERT INTO client_accounts
                (client_id, account_number, detail, delivery_date,
                 payment_date, amount, is_paid, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_cli_id,
            new_acc_num,
            acc["detail"] or "",
            acc["delivery_date"],
            acc["payment_date"],
            acc["amount"] or 0,
            acc["is_paid"] or 0,
            acc["notes"] or "",
        ))
        imported += 1

    print(f"   Importados: {imported} | Omitidos (cliente no encontrado): {skipped}")


def _migrate_settings(old, new):
    print("⚙️  Migrando configuración...")

    old_settings = old.execute("SELECT key, value FROM settings").fetchall()

    # Claves que NO queremos sobreescribir si ya existen en la nueva BD
    protected_keys = {"backup_last_date", "arca_ultimo_num_a", "arca_ultimo_num_b", "arca_ultimo_num_c"}

    imported = 0
    skipped = 0

    for s in old_settings:
        key   = s[0]
        value = s[1]

        if key in protected_keys:
            skipped += 1
            continue

        existing = new.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()

        if existing:
            # Solo actualizar si la nueva BD tiene el valor vacío
            if not existing[0] and value:
                new.execute(
                    "UPDATE settings SET value = ? WHERE key = ?", (value, key)
                )
                imported += 1
            else:
                skipped += 1
        else:
            new.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?)", (key, value)
            )
            imported += 1

    print(f"   Importados/actualizados: {imported} | Omitidos: {skipped}")


def _migrate_users(old, new):
    print("👤 Migrando usuarios...")

    old_users = old.execute("SELECT * FROM users WHERE is_active = 1").fetchall()

    existing_usernames = set(
        r[0] for r in new.execute("SELECT username FROM users").fetchall()
    )

    imported = 0
    skipped = 0

    for u in old_users:
        username = (u["username"] or "").strip()

        # No importar admin — ya existe en la nueva BD
        if username.lower() == "admin" or username in existing_usernames:
            skipped += 1
            continue

        new.execute("""
            INSERT INTO users (username, password, role, is_active)
            VALUES (?, ?, ?, 1)
        """, (
            username,
            u["password"],
            u["role"] or "ANALISTA",
        ))
        existing_usernames.add(username)
        imported += 1

    print(f"   Importados: {imported} | Omitidos (admin o duplicados): {skipped}")


if __name__ == "__main__":
    migrate()
    input("\nPresioná Enter para cerrar...")