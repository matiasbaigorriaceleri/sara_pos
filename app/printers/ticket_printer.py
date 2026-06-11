import os
import sys
import tempfile
import subprocess
import platform

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.database.database import SessionLocal
from app.models.settings_model import Setting


def get_setting(db, key, default=""):
    setting = db.query(Setting).filter(Setting.key == key).first()
    return setting.value if setting and setting.value else default


def _get_printer_name():
    db = SessionLocal()
    try:
        return get_setting(db, "printer_name", "")
    finally:
        db.close()


def generate_ticket_pdf(ticket_id, items, total, payment_method):

    db = SessionLocal()
    try:
        business_name    = get_setting(db, "business_name",    "MI NEGOCIO")
        business_address = get_setting(db, "business_address", "")
        business_phone   = get_setting(db, "business_phone",   "")
        business_cuit    = get_setting(db, "business_cuit",    "")
        ticket_legend    = get_setting(db, "ticket_legend",    "Comprobante no válido como factura")
        ticket_footer    = get_setting(db, "ticket_footer",    "Gracias por su compra")
        printer_size     = get_setting(db, "printer_size",     "80mm")
    finally:
        db.close()

    page_width = 58 * mm if "58" in printer_size else 80 * mm
    base_height = 100 * mm
    item_height = len(items) * 12 * mm
    page_height = base_height + item_height

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

    draw_text(business_name.upper(), size=11, bold=True)
    if business_address:
        draw_text(business_address, size=7)
    if business_phone:
        draw_text(f"Tel: {business_phone}", size=7)
    if ticket_legend:
        draw_text(ticket_legend, size=7)

    y -= 2 * mm
    draw_line()

    draw_text("TICKET", size=9, bold=True)
    draw_text(f"N°: {ticket_id:08d}", size=8, bold=True)
    draw_text(f"Fecha: {now.strftime('%d/%m/%Y %H:%M')}", size=7)

    y -= 1 * mm
    draw_line()

    if business_cuit:
        draw_text(f"CUIT N°: {business_cuit}", size=7)

    payment_labels = {
        "cash":     "EFECTIVO",
        "transfer": "TRANSFERENCIA",
        "qr":       "QR MERCADO PAGO",
        "budget":   "PRESUPUESTO",
    }
    method_label = payment_labels.get(payment_method, (payment_method or "").upper())
    draw_text(f"Cond. Pago: {method_label}", size=7)

    y -= 1 * mm
    draw_line()

    c.setFont("Helvetica-Bold", 7)
    c.drawString(margin, y, "Cod.")
    c.drawString(margin + 10 * mm, y, "Descripción")
    c.drawString(margin + 32 * mm, y, "Cant.")
    c.drawString(margin + 42 * mm, y, "P.U.")
    c.drawRightString(page_width - margin, y, "Sub.")
    y -= 4 * mm
    draw_line()

    for item in items:
        name     = str(item["name"])[:18]
        qty      = int(item["quantity"])
        price    = float(item["price"])
        subtotal = qty * price

        c.setFont("Helvetica", 7)
        c.drawString(margin,           y, f"{item.get('code', '')}")
        c.drawString(margin + 10 * mm, y, name)
        c.drawString(margin + 32 * mm, y, str(qty))
        c.drawString(margin + 42 * mm, y, f"{int(price):,}")
        c.drawRightString(page_width - margin, y, f"{int(subtotal):,}")
        y -= 5 * mm

    draw_line()

    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "TOTAL:")
    c.drawRightString(page_width - margin, y, f"$ {int(total):,}")
    y -= 7 * mm
    draw_line()

    if ticket_footer:
        draw_text(ticket_footer, size=7)

    c.save()
    return tmp_path


def print_ticket(ticket_id, items, total, payment_method):
    """
    Imprime el ticket en la impresora configurada o la predeterminada del sistema.
    No abre ninguna ventana ni visor — manda directo a imprimir.
    """
    try:
        pdf_path = generate_ticket_pdf(ticket_id, items, total, payment_method)
        system   = platform.system()
        printer  = _get_printer_name()

        if system == "Windows":
            _print_windows(pdf_path, printer)
        elif system == "Darwin":
            _print_unix(pdf_path, printer)
        elif system == "Linux":
            _print_unix(pdf_path, printer)

        # Limpiar PDF temporal después de un momento
        try:
            import threading
            def _cleanup():
                import time
                time.sleep(5)
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
            threading.Thread(target=_cleanup, daemon=True).start()
        except Exception:
            pass

        return True, "Ticket enviado a imprimir"

    except Exception as e:
        return False, f"Error al imprimir: {str(e)}"


def _print_windows(pdf_path, printer):
    """
    Windows: usa ShellExecute con verbo 'print' — manda directo a imprimir
    sin abrir ninguna ventana ni visor.
    Si hay SumatraPDF instalado lo usa para mayor control.
    Si hay impresora específica configurada la usa, sino usa la predeterminada.
    """
    # Intento 1: SumatraPDF (mejor control, sin ventana)
    sumatra_paths = [
        r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
        r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
    ]
    for sumatra in sumatra_paths:
        if os.path.exists(sumatra):
            if printer:
                cmd = [sumatra, "-print-to", printer, "-print-settings", "noscale", "-silent", pdf_path]
            else:
                cmd = [sumatra, "-print-to-default", "-print-settings", "noscale", "-silent", pdf_path]
            subprocess.run(cmd, check=True)
            return

    # Intento 2: ShellExecute con verbo "print" — sin abrir ventana
    import ctypes
    ret = ctypes.windll.shell32.ShellExecuteW(
        None,       # hwnd
        "print",    # verbo — manda directo a imprimir
        pdf_path,   # archivo
        None,       # parámetros
        None,       # directorio
        0           # SW_HIDE — sin ventana
    )
    if ret <= 32:
        raise Exception(f"ShellExecute falló con código {ret}")


def _print_unix(pdf_path, printer):
    """
    Mac y Linux: usa lpr directo.
    Si hay impresora configurada la usa, sino usa la predeterminada del sistema.
    lpr en Mac/Linux manda el PDF al spooler de CUPS sin abrir nada.
    """
    cmd = ["lpr"]
    if printer:
        cmd += ["-P", printer]
    # Sin opciones extra — dejar que CUPS maneje el PDF con su driver
    cmd.append(pdf_path)
    subprocess.run(cmd, check=True)