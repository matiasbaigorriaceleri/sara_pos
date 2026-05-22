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
        ticket_legend = get_setting(db, "ticket_legend", "Comprobante no válido como factura")
        ticket_footer = get_setting(db, "ticket_footer", "Gracias por su compra")
        printer_size = get_setting(db, "printer_size", "80mm")
    finally:
        db.close()

    # ── Tamaño del ticket ─────────────────────────────
    if "58" in printer_size:
        page_width = 58 * mm
    else:
        page_width = 80 * mm

    # Altura dinámica
    base_height = 100 * mm
    item_height = len(items) * 12 * mm
    page_height = base_height + item_height

    # ── Crear PDF ─────────────────────────────────────
    tmp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp_path = tmp_file.name
    tmp_file.close()

    c = canvas.Canvas(tmp_path, pagesize=(page_width, page_height))

    margin = 4 * mm
    y = page_height - 6 * mm
    center = page_width / 2

    def draw_line():
        nonlocal y
        c.setLineWidth(0.5)
        c.line(margin, y, page_width - margin, y)
        y -= 4 * mm

    def draw_text(text, size=8, bold=False, align="center"):
        nonlocal y
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, size)
        if align == "center":
            c.drawCentredString(center, y, text)
        elif align == "left":
            c.drawString(margin, y, text)
        elif align == "right":
            c.drawRightString(page_width - margin, y, text)
        y -= (size + 2) * 0.4 * mm * 2.5

    from datetime import datetime
    now = datetime.now()

    # ── Encabezado ────────────────────────────────────
    draw_text(business_name.upper(), size=11, bold=True)

    if business_address:
        draw_text(business_address, size=7)

    if business_phone:
        draw_text(f"Tel: {business_phone}", size=7)

    if ticket_legend:
        draw_text(ticket_legend, size=7)

    y -= 2 * mm
    draw_line()

    # ── Número y fecha ────────────────────────────────
    draw_text("TICKET", size=9, bold=True)
    draw_text(f"N°: {ticket_id:08d}", size=8, bold=True)
    draw_text(f"Fecha: {now.strftime('%d/%m/%Y')}", size=7)

    y -= 1 * mm
    draw_line()

    if business_cuit:
        draw_text(f"CUIT N°: {business_cuit}", size=7)

    # Método de pago
    payment_labels = {
        "cash": "EFECTIVO",
        "transfer": "TRANSFERENCIA",
        "qr": "QR MERCADO PAGO",
        "budget": "PRESUPUESTO",
    }
    method_label = payment_labels.get(payment_method, payment_method.upper() if payment_method else "")
    draw_text(f"Cond. Pago: {method_label}", size=7)

    y -= 1 * mm
    draw_line()

    # ── Encabezado columnas ───────────────────────────
    c.setFont("Helvetica-Bold", 7)
    c.drawString(margin, y, "Cod.")
    c.drawString(margin + 10 * mm, y, "Descripción")
    c.drawString(margin + 32 * mm, y, "Cant.")
    c.drawString(margin + 42 * mm, y, "P.U.")
    c.drawRightString(page_width - margin, y, "S.")
    y -= 4 * mm

    draw_line()

    # ── Items ─────────────────────────────────────────
    for item in items:
        name = str(item["name"])[:18]
        qty = int(item["quantity"])
        price = float(item["price"])
        subtotal = qty * price

        c.setFont("Helvetica", 7)
        c.drawString(margin, y, f"{item.get('code', '')}")
        c.drawString(margin + 10 * mm, y, name)
        c.drawString(margin + 32 * mm, y, str(qty))
        c.drawString(margin + 42 * mm, y, f"{int(price):,}")
        c.drawRightString(page_width - margin, y, f"{int(subtotal):,}")
        y -= 5 * mm

    draw_line()

    # ── Total ─────────────────────────────────────────
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "TOTAL:")
    c.drawRightString(page_width - margin, y, f"$ {int(total):,}")
    y -= 7 * mm

    draw_line()

    # ── Pie ───────────────────────────────────────────
    if ticket_footer:
        draw_text(ticket_footer, size=7)

    c.save()
    return tmp_path


def print_ticket(ticket_id, items, total, payment_method):

    try:
        pdf_path = generate_ticket_pdf(ticket_id, items, total, payment_method)

        system = platform.system()

        if system == "Darwin":
            subprocess.run(["lpr", pdf_path], check=True)
        elif system == "Windows":
            os.startfile(pdf_path, "print")
        elif system == "Linux":
            subprocess.run(["lpr", pdf_path], check=True)

        return True, "Ticket enviado a imprimir"

    except Exception as e:
        return False, f"Error al imprimir: {str(e)}"