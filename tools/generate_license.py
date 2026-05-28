"""
SARA+ — Generador de Licencias
================================
Script de uso INTERNO para generar claves de licencia para clientes.

Uso:
    python tools/generate_license.py

Se te pedirá el CUIT del cliente y la duración.
La clave generada la copiás y se la enviás al cliente.
"""

import sys
import os

# Agregar raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import date, timedelta
from app.utils.license_manager import generate_license, validate_license


def main():
    print("=" * 50)
    print("  SARA+ — Generador de Licencias")
    print("=" * 50)
    print()

    # CUIT
    while True:
        cuit = input("CUIT del cliente (sin guiones): ").strip().replace("-", "").replace(" ", "")
        if cuit.isdigit() and len(cuit) == 11:
            break
        print("  ⚠️  El CUIT debe tener exactamente 11 dígitos. Intentá de nuevo.")

    # Duración
    print()
    print("Duración de la licencia:")
    print("  1. 12 meses (1 año)")
    print("  2. 24 meses (2 años)")
    print("  3. Fecha personalizada")
    print()

    while True:
        opcion = input("Elegí una opción (1/2/3): ").strip()
        if opcion == "1":
            expiry = date.today() + timedelta(days=365)
            break
        elif opcion == "2":
            expiry = date.today() + timedelta(days=730)
            break
        elif opcion == "3":
            while True:
                fecha_str = input("Fecha de vencimiento (DD/MM/YYYY): ").strip()
                try:
                    from datetime import datetime
                    expiry = datetime.strptime(fecha_str, "%d/%m/%Y").date()
                    if expiry <= date.today():
                        print("  ⚠️  La fecha debe ser futura.")
                        continue
                    break
                except ValueError:
                    print("  ⚠️  Formato inválido. Usá DD/MM/YYYY.")
        else:
            print("  ⚠️  Opción inválida.")

    # Generar
    key = generate_license(cuit, expiry)

    print()
    print("=" * 50)
    print("  ✅ LICENCIA GENERADA")
    print("=" * 50)
    print()
    print(f"  CUIT:        {cuit}")
    print(f"  Vencimiento: {expiry.strftime('%d/%m/%Y')}")
    print()
    print(f"  CLAVE:")
    print(f"  {key}")
    print()

    # Verificar que la clave generada es válida
    result = validate_license(key)
    print(f"  Verificación: {result['message']}")
    print()
    print("  Copiá la clave y enviásela al cliente.")
    print("=" * 50)


if __name__ == "__main__":
    main()