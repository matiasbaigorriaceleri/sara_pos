import os
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


def _get_printer_name():
    db = SessionLocal()
    try:
        return get_setting(db, "printer_name", "")
    finally:
        db.close()


def _pdf_to_png_macos(pdf_path, printer_size):
    """
    Convierte PDF a PNG usando Python puro (Pillow + pdf2image o reportlab rasterizer).
    Fallback: usa screencapture si está disponible.
    """
    png_path = pdf_path.replace(".pdf", ".png")
    width_px = 384 if "58" in printer_size else 576  # 58mm@203dpi ≈ 384px

    # Intento 1: pdf2image (requiere poppler)
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path, dpi=203, size=(width_px, None))
        if images:
            images[0].save(png_path, "PNG")
            return png_path
    except Exception:
        pass

    # Intento 2: pillow directo
    try:
        from PIL import Image
        import struct, zlib

        # Si pdf2image no está, intentar con Wand
        from wand.image import Image as WandImage
        with WandImage(filename=f"{pdf_path}[0]", resolution=203) as img:
            img.format = "png"
            img.save(filename=png_path)
        return png_path
    except Exception:
        pass

    return None


def print_ticket(ticket_id, items, total, payment_method):

    try:
        db = SessionLocal()
        try:
            printer_size = get_setting(db, "printer_size", "80mm")
        finally:
            db.close()

        pdf_path = generate_ticket_pdf(ticket_id, items, total, payment_method)
        system   = platform.system()
        printer  = _get_printer_name()

        if system == "Darwin":
            _print_macos(pdf_path, printer, printer_size)
        elif system == "Windows":
            _print_windows(pdf_path, printer)
        elif system == "Linux":
            cmd = ["lpr"]
            if printer:
                cmd += ["-P", printer]
            cmd.append(pdf_path)
            subprocess.run(cmd, check=True)

        return True, "Ticket enviado a imprimir"

    except Exception as e:
        return False, f"Error al imprimir: {str(e)}"


def _print_macos(pdf_path, printer, printer_size):
    """
    Estrategia para macOS con impresoras térmicas:
    1. Intentar con pdf2image → PNG → lpr
    2. Intentar con mdimport/qlmanage para rasterizar
    3. Fallback: lpr con -o media personalizado
    """
    width_px = 384 if "58" in printer_size else 576

    # ── Intento 1: pdf2image ──────────────────────────
    try:
        from pdf2image import convert_from_path
        png_path = pdf_path.replace(".pdf", ".png")
        images = convert_from_path(pdf_path, dpi=203, size=(width_px, None))
        if images:
            images[0].save(png_path, "PNG")
            cmd = ["lpr"]
            if printer:
                cmd += ["-P", printer]
            cmd += ["-o", "fit-to-page", png_path]
            subprocess.run(cmd, check=True)
            os.remove(png_path)
            return
    except Exception:
        pass

    # ── Intento 2: qlmanage para rasterizar el PDF ────
    try:
        png_dir = tempfile.mkdtemp()
        subprocess.run([
            "qlmanage", "-t", "-s", str(width_px), "-o", png_dir, pdf_path
        ], check=True, capture_output=True)

        # qlmanage genera archivo con nombre original + .png
        import glob
        pngs = glob.glob(os.path.join(png_dir, "*.png"))
        if pngs:
            cmd = ["lpr"]
            if printer:
                cmd += ["-P", printer]
            cmd += ["-o", "fit-to-page", pngs[0]]
            subprocess.run(cmd, check=True)
            for f in pngs:
                os.remove(f)
            os.rmdir(png_dir)
            return
    except Exception:
        pass

    # ── Intento 3: lpr con opciones de papel personalizado ──
    # Último recurso — manda el PDF pero con opciones que
    # le dicen a CUPS cómo manejarlo
    cmd = ["lpr"]
    if printer:
        cmd += ["-P", printer]

    # Opciones para papel térmico
    media = "Custom.58x200mm" if "58" in printer_size else "Custom.80x200mm"
    cmd += [
        "-o", f"media={media}",
        "-o", "fit-to-page",
        "-o", "ColorModel=Gray",
        pdf_path
    ]
    subprocess.run(cmd, check=True)


def _print_windows(pdf_path, printer):
    sumatra_paths = [
        r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
        r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
    ]
    for sumatra in sumatra_paths:
        if os.path.exists(sumatra):
            cmd = [sumatra, "-print-to", printer, "-print-settings", "noscale", pdf_path] if printer else [sumatra, "-print-to-default", pdf_path]
            subprocess.run(cmd, check=True)
            return
    os.startfile(pdf_path, "print")