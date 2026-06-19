"""
SARA+ — License Manager
=======================
Lógica de generación y validación de licencias.

Formato de clave: SARA-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXX
Estructura interna (27 chars sin prefijo ni guiones):
    {CUIT 11 digits}{DATE 8 digits YYYYMMDD}{SIGNATURE 8 chars}

El SIGNATURE es HMAC-SHA256 truncado de "{CUIT}{DATE}" con clave secreta interna.
"""

import os
import sys
import hmac
import hashlib
from datetime import datetime, date

# ── Clave secreta interna ─────────────────────────────
# IMPORTANTE: No cambiar una vez en producción o todas las licencias emitidas
# dejarán de funcionar. Guardá esto en un lugar seguro.
_SECRET = b"SARA_POS_2024_SECRET_KEY_NO_COMPARTIR"


def _sign(payload: str) -> str:
    """Genera firma HMAC-SHA256 truncada a 8 chars en mayúsculas."""
    return hmac.new(_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest()[:8].upper()


def generate_license(cuit: str, expiry_date: date) -> str:
    """
    Genera una clave de licencia SARA+.

    Args:
        cuit: CUIT del cliente sin guiones (ej: "20123456789")
        expiry_date: fecha de vencimiento (objeto date)

    Returns:
        Clave con formato SARA-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXX
    """
    cuit = cuit.replace("-", "").replace(" ", "")
    date_str = expiry_date.strftime("%Y%m%d")
    payload = f"{cuit}{date_str}"
    sig = _sign(payload)
    raw = f"{payload}{sig}"   # 11 + 8 + 8 = 27 chars

    # Dividir en grupos de 4
    chunks = [raw[i:i+4] for i in range(0, len(raw), 4)]
    return "SARA-" + "-".join(chunks)


def validate_license(key: str) -> dict:
    """
    Valida una clave de licencia.

    Returns dict con:
        valid (bool): si la clave es válida y no está vencida
        plan (str): 'SARA+' o 'FREE'
        expiry (date | None): fecha de vencimiento
        cuit (str | None): CUIT asociado
        message (str): mensaje descriptivo
    """
    result = {
        "valid": False,
        "plan": "FREE",
        "expiry": None,
        "cuit": None,
        "message": "",
    }

    if not key or not key.upper().startswith("SARA-"):
        result["message"] = "Clave inválida"
        return result

    try:
        body = key.upper()[5:].replace("-", "")

        if len(body) != 27:
            result["message"] = "Formato de clave incorrecto"
            return result

        cuit = body[:11]
        date_str = body[11:19]
        sig = body[19:27]

        # Verificar firma
        payload = f"{cuit}{date_str}"
        expected_sig = _sign(payload)
        if not hmac.compare_digest(sig, expected_sig):
            result["message"] = "Clave inválida o modificada"
            return result

        # Verificar fecha
        expiry = datetime.strptime(date_str, "%Y%m%d").date()
        today = date.today()

        result["cuit"] = cuit
        result["expiry"] = expiry

        if today > expiry:
            result["valid"] = False
            result["plan"] = "FREE"
            result["message"] = f"Licencia vencida el {expiry.strftime('%d/%m/%Y')}. El sistema opera en modo FREE."
        else:
            days_left = (expiry - today).days
            result["valid"] = True
            result["plan"] = "SARA+"
            result["message"] = f"Licencia SARA+ activa. Vence el {expiry.strftime('%d/%m/%Y')} ({days_left} días restantes)."

    except Exception as e:
        result["message"] = f"Error al procesar la clave: {str(e)}"

    return result


def _get_license_path():
    """Ruta donde se guarda la clave de licencia."""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
    return os.path.join(base, "license.key")


def save_license(key: str):
    """Guarda la clave en disco."""
    with open(_get_license_path(), "w", encoding="utf-8") as f:
        f.write(key.strip())


def load_license() -> str:
    """Carga la clave desde disco. Devuelve string vacío si no existe."""
    path = _get_license_path()
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def get_current_plan() -> dict:
    """
    Devuelve el estado de licencia actual del sistema.
    Es el método principal que usa el resto de la app.

    Returns el mismo dict que validate_license().
    Si no hay clave guardada, devuelve plan FREE.
    """
    key = load_license()
    if not key:
        return {
            "valid": False,
            "plan": "FREE",
            "expiry": None,
            "cuit": None,
            "message": "Sin licencia activa. Operando en modo FREE.",
        }
    return validate_license(key)


# ── Restricciones por plan ────────────────────────────

PLAN_LIMITS = {
    "FREE": {
        "max_products": None,    # ilimitado
        "max_clients": None,     # ilimitado
        "max_users": 2,
        "suppliers": False,
        "reports": False,
        "email": False,
        "backup": False,
        "arca": False,
        "postgresql": False,
        "ticket_watermark": True,
    },
    "SARA+": {
        "max_products": None,    # ilimitado
        "max_clients": None,     # ilimitado
        "max_users": None,       # ilimitado
        "suppliers": True,
        "reports": True,
        "email": True,
        "backup": True,
        "arca": True,
        "postgresql": True,
        "ticket_watermark": False,
    },
}


def get_plan_limits() -> dict:
    """Devuelve el dict de límites del plan activo."""
    plan = get_current_plan()["plan"]
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["FREE"])


def is_feature_allowed(feature: str) -> bool:
    """
    Verifica si una feature está habilitada en el plan actual.
    feature puede ser: 'suppliers', 'reports', 'email', 'backup',
                       'arca', 'postgresql', 'ticket_watermark'
    """
    limits = get_plan_limits()
    return bool(limits.get(feature, False))


def check_limit(resource: str, current_count: int) -> tuple:
    """
    Verifica si se puede agregar un recurso más.

    Args:
        resource: 'products', 'clients' o 'users'
        current_count: cantidad actual

    Returns:
        (allowed: bool, message: str)
    """
    limits = get_plan_limits()
    key = f"max_{resource}"
    limit = limits.get(key)

    if limit is None:
        return True, ""

    if current_count >= limit:
        plan = get_current_plan()["plan"]
        return False, (
            f"Límite del plan {plan} alcanzado: máximo {limit} {resource}.\n"
            f"Activá SARA+ para acceso ilimitado."
        )

    return True, ""