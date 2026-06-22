"""
SARA POS — Notificador de registro a BIMABA
============================================
Envía por email a soportesara@bimaba.com los datos que el usuario
completa en el wizard de configuración inicial (paso "Registro personal").

IMPORTANTE: este módulo usa una cuenta de correo PROPIA de BIMABA
(contactossara@bimaba.com), totalmente independiente de la configuración
SMTP que cada cliente carga en Configuración → Email para sus propios
tickets/presupuestos. El wizard NO depende de ninguna configuración
hecha por el usuario: funciona siempre, desde el primer arranque.

El envío se hace en un hilo aparte para no congelar la UI, y cualquier
error (sin internet, servidor caído, etc.) se ignora silenciosamente:
nunca debe trabar el wizard ni mostrar errores al usuario final.
"""

import smtplib
import threading

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


# ── Credenciales propias de BIMABA (hardcodeadas, NO tocar desde Configuración) ──
_SMTP_HOST = "c2781833.ferozo.com"
_SMTP_PORT = 465  # SSL
_SMTP_USER = "contactossara@bimaba.com"
_SMTP_PASSWORD = "S4r4POs2026/@*"

_DESTINATARIO = "soportesara@bimaba.com"


def _build_email(data: dict) -> MIMEMultipart:
    msg = MIMEMultipart()
    msg["From"] = _SMTP_USER
    msg["To"] = _DESTINATARIO
    msg["Subject"] = f"nuevo_cliente — {data.get('nombre', '')} {data.get('apellido', '')}"

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    body = f"""Nuevo registro completado en el wizard de SARA POS.

Fecha: {fecha}

── Datos personales ──
Nombre:     {data.get('nombre', '')}
Apellido:   {data.get('apellido', '')}
Email:      {data.get('email', '')}
Teléfono:   {data.get('phone', '') or '(no informado)'}
País:       {data.get('pais', '') or '(no informado)'}
Ciudad:     {data.get('ciudad', '') or '(no informado)'}
Localidad:  {data.get('localidad', '') or '(no informado)'}

── Negocio (si ya lo completó) ──
Nombre del negocio: {data.get('business_name', '') or '(pendiente)'}

---
Este email fue generado automáticamente por SARA POS al completar
el wizard de configuración inicial. No responder a este correo.
"""

    msg.attach(MIMEText(body, "plain", "utf-8"))
    return msg


def _send_sync(data: dict):
    try:
        msg = _build_email(data)
        with smtplib.SMTP_SSL(_SMTP_HOST, _SMTP_PORT, timeout=10) as server:
            server.login(_SMTP_USER, _SMTP_PASSWORD)
            server.sendmail(_SMTP_USER, [_DESTINATARIO], msg.as_string())
    except Exception:
        # Silencioso a propósito: sin internet, servidor caído, etc.
        # El wizard NUNCA debe trabarse ni mostrar error por esto.
        pass


def send_lead_to_bimaba(data: dict):
    """
    Envía los datos del registro a BIMABA en un hilo aparte (no bloqueante).

    data esperado (todas las claves son opcionales salvo nombre/apellido/email):
        {
            "nombre": str,
            "apellido": str,
            "email": str,
            "phone": str,
            "pais": str,
            "ciudad": str,
            "localidad": str,
            "business_name": str,
        }
    """
    thread = threading.Thread(target=_send_sync, args=(data,), daemon=True)
    thread.start()
