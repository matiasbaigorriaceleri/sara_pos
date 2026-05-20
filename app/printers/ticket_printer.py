import os
import tempfile
import subprocess
import platform

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.database.database import SessionLocal
from app.models.settings_model import Setting


def get_setting(db, key, default=""):
    setting = db.query(Setting).filter(
        Setting.key == key
    ).first()
    return setting.value if setting and setting.value else default


def generate_ticket_pdf(ticket_id, items, total, payment_method):

    db = SessionLocal()

    try:
        business_name = get_setting(db, "business_name", "MI NEGOCIO")
        business_address = get_setting(db, "business_address", "")
        business_phone = get_setting(db, "business_phone", "")
        business_cuit = get_setting(db, "business_cuit", "")
        ticket_footer = get_setting(db, "ticket_footer", "Gracias por su compra")
        printer_size = get_setting(db, "printer_size", "80mm")
    finally:
        db.close()

    # ── Tamaño del ticket ─────────────────────────────
    if "58" in printer_size:
        page_width = 58 * mm
    else:
        page_width = 80 * mm

    # Calcular altura dinámica según items
    base_height = 80 * mm
    item_height = len(items) * 10 * mm
    page_height = base_height + item_height

    # ── Crear PDF temporal ────────────────────────────
    tmp_file = tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False
    )
    tmp_path = tmp_file.name
    tmp_file.close()

    c = canvas.Canvas(tmp_path, pagesize=(page_width, page_height))

    margin = 4 * mm
    y = page_height - 8 * mm
    center = page_width / 2

    def line_separator():
        nonlocal y
        c.setLineWidth(0.5)
        c.line(margin, y, page_width - margin, y)
        y -= 5 * mm

    def add_text(text, size=8, bold=False, align="center"):
        nonlocal y
        if bold:
            c.setFont("Helvetica-Bold", size)
        else:
            c.setFont("Helvetica", size)
        if align == "center":
            c.drawCentredString(center, y, text)
        elif align == "left":
            c.drawString(margin, y, text)
        elif align == "right":
            c.drawRightString(page_width - margin, y, text)
        y -= (size + 3) * 0.352778 * mm * 2.2

    # ── Encabezado ────────────────────────────────────
    add_text(business_name.upper(), size=12, bold=True)

    if business_address:
        add_text(business_address, size=7)

    if business_phone:
        add_text(f"Tel: {business_phone}", size=7)

    if business_cuit:
        add_text(f"CUIT: {business_cuit}", size=7)

    add_text(f"Ticket N° {ticket_id:05d}", size=8, bold=True)

    from datetime import datetime
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    add_text(now, size=7)

    line_separator()

    # ── Items ─────────────────────────────────────────
    add_text("PRODUCTOS", size=8, bold=True)
    y -= 2 * mm

    for item in items:
        name = item["name"]
        qty = int(item["quantity"])
        price = float(item["price"])
        subtotal = qty * price

        # Nombre del producto
        c.setFont("Helvetica", 7)
        c.drawString(margin, y, f"{name}")
        y -= 4 * mm

        # Cantidad x precio = subtotal
        c.setFont("Helvetica", 7)
        c.drawString(margin, y, f"  {qty} x $ {int(price)}")
        c.drawRightString(page_width - margin, y, f"$ {int(subtotal)}")
        y -= 5 * mm

    line_separator()

    # ── Total ─────────────────────────────────────────
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "TOTAL")
    c.drawRightString(page_width - margin, y, f"$ {int(total)}")
    y -= 7 * mm

    # ── Método de pago ────────────────────────────────
    payment_labels = {
        "cash": "Efectivo",
        "transfer": "Transferencia",
        "qr": "QR Mercado Pago",
        "budget": "Presupuesto",
    }
    label = payment_labels.get(payment_method, payment_method)
    add_text(f"Pago: {label}", size=8)

    line_separator()

    # ── Pie ───────────────────────────────────────────
    if ticket_footer:
        add_text(ticket_footer, size=7)

    c.save()

    return tmp_path


def print_ticket(ticket_id, items, total, payment_method):

    try:
        pdf_path = generate_ticket_pdf(
            ticket_id,
            items,
            total,
            payment_method
        )

        system = platform.system()

        if system == "Darwin":
            # macOS
            subprocess.run(
                ["lpr", pdf_path],
                check=True
            )

        elif system == "Windows":
            # Windows
            os.startfile(pdf_path, "print")

        elif system == "Linux":
            # Linux
            subprocess.run(
                ["lpr", pdf_path],
                check=True
            )

        return True, "Ticket enviado a imprimir"

    except Exception as e:
        return False, f"Error al imprimir: {str(e)}"