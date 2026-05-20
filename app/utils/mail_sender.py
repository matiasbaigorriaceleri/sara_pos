import smtplib
import tempfile
import os

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from app.database.database import SessionLocal
from app.models.settings_model import Setting
from app.printers.ticket_printer import generate_ticket_pdf


def get_setting(db, key, default=""):
    setting = db.query(Setting).filter(
        Setting.key == key
    ).first()
    return setting.value if setting and setting.value else default


def send_budget_email(to_email, ticket_id, cart, total):

    db = SessionLocal()

    try:
        smtp_host = get_setting(db, "smtp_host", "")
        smtp_port = get_setting(db, "smtp_port", "587")
        smtp_email = get_setting(db, "smtp_email", "")
        smtp_password = get_setting(db, "smtp_password", "")
        business_name = get_setting(db, "business_name", "SARA POS")
    finally:
        db.close()

    if not smtp_host or not smtp_email or not smtp_password:
        return False, "Configure el email SMTP en Configuración antes de enviar"

    # ── Generar PDF ───────────────────────────────────
    try:
        pdf_path = generate_ticket_pdf(
            ticket_id,
            cart,
            total,
            "budget"
        )
    except Exception as e:
        return False, f"Error al generar PDF: {str(e)}"

    # ── Armar email ───────────────────────────────────
    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_email
        msg["To"] = to_email
        msg["Subject"] = f"Presupuesto N° {ticket_id:05d} - {business_name}"

        body = f"""
Estimado cliente,

Adjunto encontrará el presupuesto N° {ticket_id:05d} por un total de $ {int(total)}.

Gracias por contactarnos.

{business_name}
        """.strip()

        msg.attach(MIMEText(body, "plain"))

        # Adjuntar PDF
        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename=presupuesto_{ticket_id:05d}.pdf"
            )
            msg.attach(part)

        # ── Enviar ────────────────────────────────────
        port = int(smtp_port) if smtp_port.isdigit() else 587

        with smtplib.SMTP(smtp_host, port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, to_email, msg.as_string())

        return True, f"Presupuesto enviado a {to_email}"

    except Exception as e:
        return False, f"Error al enviar email: {str(e)}"

    finally:
        try:
            os.unlink(pdf_path)
        except:
            pass