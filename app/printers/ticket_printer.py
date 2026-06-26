import os
import sys
import tempfile
import subprocess
import platform
from datetime import datetime

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


def _get_ticket_data(ticket_id, items, total, payment_method):
    """
    Junta todos los datos necesarios para armar el ticket
    (configuración del negocio + datos de la venta), para que
    tanto la rama PDF (Mac/Linux) como la rama GDI (Windows)
    dibujen exactamente el mismo contenido.
    """
    db = SessionLocal()
    try:
        business_name    = get_setting(db, "business_name",    "MI NEGOCIO")
        business_address = get_setting(db, "business_address", "")
        business_phone   = get_setting(db, "business_phone",   "")
        business_cuit     = get_setting(db, "business_cuit",    "")
        ticket_legend     = get_setting(db, "ticket_legend",    "Comprobante no válido como factura")
        ticket_footer     = get_setting(db, "ticket_footer",    "Gracias por su compra")
        printer_size      = get_setting(db, "printer_size",     "80mm")
    finally:
        db.close()

    payment_labels = {
        "cash":     "EFECTIVO",
        "transfer": "TRANSFERENCIA",
        "qr":       "QR MERCADO PAGO",
        "budget":   "PRESUPUESTO",
    }
    method_label = payment_labels.get(payment_method, (payment_method or "").upper())

    return {
        "business_name":    business_name,
        "business_address": business_address,
        "business_phone":   business_phone,
        "business_cuit":    business_cuit,
        "ticket_legend":    ticket_legend,
        "ticket_footer":    ticket_footer,
        "printer_size":     printer_size,
        "paper_width_mm":   58 if "58" in printer_size else 80,
        "ticket_id":        ticket_id,
        "items":            items,
        "total":            total,
        "method_label":     method_label,
        "now":              datetime.now(),
    }


# ──────────────────────────────────────────────────────────
# Generación de PDF (usado en Mac/Linux)
# ──────────────────────────────────────────────────────────

def generate_ticket_pdf(ticket_id, items, total, payment_method):
    data = _get_ticket_data(ticket_id, items, total, payment_method)
    page_width = data["paper_width_mm"] * mm
    base_height = 50 * mm
    item_height = len(items) * 4 * mm
    page_height = base_height + item_height

    tmp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp_path = tmp_file.name
    tmp_file.close()

    c = canvas.Canvas(tmp_path, pagesize=(page_width, page_height))
    _draw_ticket_reportlab(c, page_width, page_height, data)
    c.save()
    return tmp_path


from reportlab.pdfbase.pdfmetrics import stringWidth


def _draw_ticket_reportlab(c, page_width, page_height, data):
    margin = 3 * mm
    y = page_height - 5 * mm
    center = page_width / 2
    content_left = margin
    content_right = page_width - margin
    usable_width = content_right - content_left

    def line_gap(size):
        return size * 0.40 * mm + 1.4 * mm

    def fit_size(text, max_size, font_name, max_width):
        size = max_size
        while size > 5.5 and stringWidth(text, font_name, size) > max_width:
            size -= 0.5
        return size

    def draw(text, size=7, bold=False, align="center", gap=None, autofit=False):
        nonlocal y
        font = "Helvetica-Bold" if bold else "Helvetica"
        if autofit:
            size = fit_size(text, size, font, usable_width)
        c.setFont(font, size)
        if align == "center":
            c.drawCentredString(center, y, text)
        elif align == "left":
            c.drawString(content_left, y, text)
        elif align == "right":
            c.drawRightString(content_right, y, text)
        y -= gap if gap is not None else line_gap(size)

    def hr(gap_before=0.3, gap_after=1.0, dashed=False):
        nonlocal y
        y -= gap_before * mm
        c.setLineWidth(0.4)
        if dashed:
            c.setDash(1, 1.2)
        c.line(content_left, y, content_right, y)
        c.setDash()
        y -= gap_after * mm

    # ── Encabezado (centrado) ──
    draw(data["business_name"].upper(), size=10, bold=True, align="center", autofit=True)
    if data["business_address"]:
        draw(data["business_address"], size=6.5, align="center", autofit=True)
    if data["business_phone"]:
        draw(f"Tel: {data['business_phone']}", size=6.5, align="center")
    if data["business_cuit"]:
        draw(f"CUIT: {data['business_cuit']}", size=6.5, align="center")

    hr(gap_before=0.6, gap_after=2.0)
    draw("Ticket de compra", size=7.5, bold=True, align="center")
    y -= 0.3 * mm

    col_mid = content_left + usable_width * 0.5
    c.setFont("Helvetica", 6.5)
    c.drawString(content_left, y, f"Fecha: {data['now'].strftime('%d/%m/%Y')}")
    c.drawRightString(content_right, y, f"Hora: {data['now'].strftime('%H:%M')}")
    y -= line_gap(6.5)
    c.drawString(content_left, y, f"N°: {data['ticket_id']:08d}")
    c.drawRightString(content_right, y, f"Pago: {data['method_label']}")
    y -= line_gap(6.5)

    hr(gap_before=0.6, gap_after=1.6)

    # ── Tabla de items (una sola línea por item: Desc | Cant | Importe) ──
    col_cant_x  = content_left + usable_width * 0.68
    col_importe = content_right

    c.setFont("Helvetica-Bold", 6.5)
    c.drawString(content_left, y, "Descripción")
    c.drawCentredString(col_cant_x, y, "Cant.")
    c.drawRightString(col_importe, y, "Importe")
    y -= line_gap(6.5)
    hr(gap_before=0.6, gap_after=2.2)

    max_chars = 20 if data["paper_width_mm"] <= 58 else 28

    for item in data["items"]:
        name     = str(item["name"])[:max_chars]
        qty      = int(item["quantity"])
        price    = float(item["price"])
        subtotal = qty * price

        c.setFont("Helvetica", 6.5)
        c.drawString(content_left, y, name)
        c.drawCentredString(col_cant_x, y, str(qty))
        c.drawRightString(col_importe, y, f"{subtotal:,.0f}")
        y -= line_gap(6.5)

    hr(gap_before=0.6, gap_after=2.4)

    # ── Total ──
    c.setFont("Helvetica-Bold", 9)
    c.drawString(content_left, y, "Total:")
    c.drawRightString(content_right, y, f"$ {data['total']:,.0f}")
    y -= line_gap(9) + 0.5 * mm

    hr(gap_before=0.3, gap_after=1.8, dashed=True)

    # ── Pie (centrado) ──
    if data["ticket_legend"]:
        draw(data["ticket_legend"], size=5.8, align="center")
    if data["ticket_footer"]:
        y -= 0.4 * mm
        draw(data["ticket_footer"], size=7, bold=True, align="center")

    y -= 1.2 * mm
    draw("BIMABA™ - SARA POS", size=5, align="center")


# ──────────────────────────────────────────────────────────
# Impresión directa por GDI en Windows (sin PDF, sin visores)
# ──────────────────────────────────────────────────────────

def _print_windows_gdi(data, printer_name):
    """
    Dibuja el ticket directo sobre el Device Context de la impresora
    usando win32print/win32ui. En vez de asumir que el ancho de papel
    configurado (58/80mm) es el área imprimible real, se consulta el
    driver (HORZRES/LOGPIXELSX) para obtener el ancho útil REAL —
    muchos drivers térmicos genéricos (ej. "POS-58") tienen márgenes
    no imprimibles de varios mm que de otro modo cortan el contenido
    o lo descentran.
    """
    import win32print
    import win32ui
    from win32con import MM_TEXT, LOGPIXELSX, LOGPIXELSY, HORZRES

    target_printer = printer_name or win32print.GetDefaultPrinter()

    hdc = win32ui.CreateDC()
    hdc.CreatePrinterDC(target_printer)
    hdc.SetMapMode(MM_TEXT)

    dpi_x = hdc.GetDeviceCaps(LOGPIXELSX) or 203
    dpi_y = hdc.GetDeviceCaps(LOGPIXELSY) or 203
    printable_width_px = hdc.GetDeviceCaps(HORZRES)

    px_per_mm_x = dpi_x / 25.4
    px_per_mm_y = dpi_y / 25.4

    if printable_width_px and printable_width_px > 10:
        page_width_px = printable_width_px
    else:
        page_width_px = int(data["paper_width_mm"] * px_per_mm_x)

    page_height_mm = 55 + len(data["items"]) * 4
    page_height_px = int(page_height_mm * px_per_mm_y)

    hdc.StartDoc(f"SARA POS Ticket {data['ticket_id']:08d}")
    hdc.StartPage()

    _draw_ticket_gdi(hdc, page_width_px, page_height_px, data, px_per_mm_x, px_per_mm_y)

    hdc.EndPage()
    hdc.EndDoc()


def _draw_ticket_gdi(hdc, page_width, page_height, data, px_per_mm_x, px_per_mm_y):
    """
    MM_TEXT: 1 unidad lógica = 1 píxel, origen arriba-izquierda, Y
    creciendo hacia abajo (igual que la mayoría de las APIs gráficas
    "naturales") — no hace falta negar coordenadas como con MM_TWIPS.
    """
    import win32ui

    def mmx(v):
        return int(v * px_per_mm_x)

    def mmy(v):
        return int(v * px_per_mm_y)

    margin = mmx(2.5)
    content_left = margin
    content_right = page_width - margin
    usable_width = content_right - content_left
    center = page_width // 2
    y = mmy(4)

    def font(size_pt, bold=False):
        # height en píxeles lógicos: size_pt (1/72") -> px a dpi_y real.
        height_px = int(size_pt / 72 * px_per_mm_y * 25.4)
        return win32ui.CreateFont({
            "name": "Arial",
            "height": -height_px,
            "weight": 700 if bold else 400,
        })

    def line_gap(size_pt):
        return int(size_pt / 72 * px_per_mm_y * 25.4 * 1.5)

    def draw(text, size=7, bold=False, align="center", autofit=False):
        nonlocal y
        if autofit:
            s = size
            while s > 5.5:
                fnt_test = font(s, bold)
                hdc.SelectObject(fnt_test)
                w_test, _ = hdc.GetTextExtent(text)
                if w_test <= usable_width:
                    break
                s -= 0.5
            size = s
        fnt = font(size, bold)
        hdc.SelectObject(fnt)
        w, h = hdc.GetTextExtent(text)
        if align == "center":
            x = center - w // 2
        elif align == "right":
            x = content_right - w
        else:
            x = content_left
        hdc.TextOut(x, y, text)
        y += line_gap(size)

    def hr(gap_before_mm=0.8, gap_after_mm=2.0):
        nonlocal y
        y += mmy(gap_before_mm)
        pen = win32ui.CreatePen(0, 1, 0)
        old_pen = hdc.SelectObject(pen)
        hdc.MoveTo((content_left, y))
        hdc.LineTo((content_right, y))
        hdc.SelectObject(old_pen)
        y += mmy(gap_after_mm)

    def row(left_txt, right_txt, size=6.5, bold=False):
        nonlocal y
        fnt = font(size, bold)
        hdc.SelectObject(fnt)
        hdc.TextOut(content_left, y, left_txt)
        w, h = hdc.GetTextExtent(right_txt)
        hdc.TextOut(content_right - w, y, right_txt)
        y += line_gap(size)

    def row3(left_txt, mid_txt, right_txt, size=6.5, bold=False):
        nonlocal y
        fnt = font(size, bold)
        hdc.SelectObject(fnt)
        hdc.TextOut(content_left, y, left_txt)
        mid_x = content_left + int(usable_width * 0.68)
        mw, _ = hdc.GetTextExtent(mid_txt)
        hdc.TextOut(mid_x - mw // 2, y, mid_txt)
        rw, h = hdc.GetTextExtent(right_txt)
        hdc.TextOut(content_right - rw, y, right_txt)
        y += line_gap(size)

    max_chars = 20 if data["paper_width_mm"] <= 58 else 28

    # ── Encabezado (centrado) ──
    draw(data["business_name"].upper(), size=10, bold=True, align="center", autofit=True)
    if data["business_address"]:
        draw(data["business_address"], size=6.5, align="center", autofit=True)
    if data["business_phone"]:
        draw(f"Tel: {data['business_phone']}", size=6.5, align="center")
    if data["business_cuit"]:
        draw(f"CUIT: {data['business_cuit']}", size=6.5, align="center")

    hr(gap_before_mm=0.6, gap_after_mm=2.0)

    # ── Título + fecha/hora + comprobante ──
    draw("Ticket de compra", size=7.5, bold=True, align="center")
    row(f"Fecha: {data['now'].strftime('%d/%m/%Y')}", f"Hora: {data['now'].strftime('%H:%M')}", size=6.5)
    row(f"N°: {data['ticket_id']:08d}", f"Pago: {data['method_label']}", size=6.5)

    hr(gap_before_mm=0.6, gap_after_mm=2.0)

    # ── Tabla de items ──
    row3("Descripción", "Cant.", "Importe", size=6.5, bold=True)
    hr(gap_before_mm=0.3, gap_after_mm=2.2)

    for item in data["items"]:
        name     = str(item["name"])[:max_chars]
        qty      = int(item["quantity"])
        price    = float(item["price"])
        subtotal = qty * price
        row3(name, str(qty), f"{subtotal:,.0f}", size=6.5)

    hr(gap_before_mm=0.6, gap_after_mm=2.4)

    # ── Total ──
    row("Total:", f"$ {data['total']:,.0f}", size=9, bold=True)
    y += mmy(0.5)

    hr(gap_before_mm=0.3, gap_after_mm=1.8)

    # ── Pie (centrado) ──
    if data["ticket_legend"]:
        draw(data["ticket_legend"], size=5.8, align="center")
    if data["ticket_footer"]:
        draw(data["ticket_footer"], size=7, bold=True, align="center")

    draw("BIMABA™ - SARA POS", size=5, align="center")


# ──────────────────────────────────────────────────────────
# Punto de entrada público
# ──────────────────────────────────────────────────────────

def print_ticket(ticket_id, items, total, payment_method):
    """
    Imprime el ticket en la impresora configurada o la predeterminada.
    En Windows dibuja directo por GDI (sin PDF, sin visores externos).
    En Mac/Linux genera un PDF de tamaño exacto y lo manda a lpr,
    forzando el tamaño de papel custom para que CUPS no lo encuadre
    en A4/Letter.
    """
    try:
        system  = platform.system()
        printer = _get_printer_name()

        if system == "Windows":
            data = _get_ticket_data(ticket_id, items, total, payment_method)
            _print_windows_gdi(data, printer)
        else:
            pdf_path = generate_ticket_pdf(ticket_id, items, total, payment_method)
            _print_unix(pdf_path, printer,
                        _get_ticket_data(ticket_id, items, total, payment_method)["paper_width_mm"])
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


def _print_unix(pdf_path, printer, paper_width_mm):
    """
    Mac y Linux: usa lpr, forzando el tamaño de papel custom explícito
    (en puntos: 1mm = 2.83465pt) para que CUPS no encuadre el ticket
    angosto dentro de una hoja A4/Letter por defecto.
    """
    width_pt = int(paper_width_mm * 2.83465)
    # Alto grande: el driver de la térmica recorta al largo real impreso.
    height_pt = int(1000 * 2.83465)

    cmd = ["lpr"]
    if printer:
        cmd += ["-P", printer]
    cmd += ["-o", f"media=Custom.{width_pt}x{height_pt}pt"]
    cmd += ["-o", "fit-to-page"]
    cmd.append(pdf_path)
    subprocess.run(cmd, check=True)