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
    base_height = 95 * mm
    item_height = len(items) * 5.5 * mm
    page_height = base_height + item_height

    tmp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp_path = tmp_file.name
    tmp_file.close()

    c = canvas.Canvas(tmp_path, pagesize=(page_width, page_height))
    _draw_ticket_reportlab(c, page_width, page_height, data)
    c.save()
    return tmp_path


def _draw_ticket_reportlab(c, page_width, page_height, data):
    margin = 3.5 * mm
    y = page_height - 6 * mm
    center = page_width / 2
    content_left = margin
    content_right = page_width - margin

    def line_gap(size):
        return (size + 2.6) * 0.55 * mm

    def draw(text, size=8, bold=False, align="center", gap=None):
        nonlocal y
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, size)
        if align == "center":
            c.drawCentredString(center, y, text)
        elif align == "left":
            c.drawString(content_left, y, text)
        elif align == "right":
            c.drawRightString(content_right, y, text)
        y -= gap if gap is not None else line_gap(size)

    def hr(gap_before=1.2, gap_after=1.6, dashed=False):
        nonlocal y
        y -= gap_before * mm
        c.setLineWidth(0.5)
        if dashed:
            c.setDash(1, 1.3)
        c.line(content_left, y, content_right, y)
        c.setDash()
        y -= gap_after * mm

    # ── Encabezado (centrado) ──
    draw(data["business_name"].upper(), size=11, bold=True, align="center")
    if data["business_address"]:
        draw(data["business_address"], size=7, align="center")
    if data["business_phone"]:
        draw(f"Tel: {data['business_phone']}", size=7, align="center")
    if data["business_cuit"]:
        draw(f"CUIT: {data['business_cuit']}", size=7, align="center")

    hr(gap_before=1.5, gap_after=1.8)

    # ── Datos del comprobante (izquierda) ──
    draw("TICKET DE VENTA", size=9, bold=True, align="center")
    y -= 0.8 * mm
    draw(f"N° {data['ticket_id']:08d}", size=8, bold=False, align="left")
    draw(data["now"].strftime("%d/%m/%Y  %H:%M"), size=7, align="left")
    draw(f"Forma de pago: {data['method_label']}", size=7, align="left")

    hr(gap_before=1.5, gap_after=1.8)

    # ── Tabla de items ──
    col_qty   = content_left + 28 * mm
    col_price = content_left + 38 * mm

    c.setFont("Helvetica-Bold", 7)
    c.drawString(content_left, y, "DESCRIPCIÓN")
    c.drawCentredString(col_qty, y, "CANT")
    c.drawRightString(content_right, y, "IMPORTE")
    y -= 3.2 * mm
    hr(gap_before=0.4, gap_after=1.4)

    for item in data["items"]:
        name     = str(item["name"])[:24]
        qty      = int(item["quantity"])
        price    = float(item["price"])
        subtotal = qty * price

        c.setFont("Helvetica", 7.5)
        c.drawString(content_left, y, name)
        y -= 3.4 * mm
        c.setFont("Helvetica", 7)
        c.drawString(content_left + 2 * mm, y, f"{qty} x $ {price:,.0f}")
        c.drawRightString(content_right, y, f"$ {subtotal:,.0f}")
        y -= 4.4 * mm

    hr(gap_before=0.8, gap_after=1.8)

    # ── Total ──
    c.setFont("Helvetica-Bold", 11)
    c.drawString(content_left, y, "TOTAL")
    c.drawRightString(content_right, y, f"$ {data['total']:,.0f}")
    y -= 6 * mm

    hr(gap_before=0.5, gap_after=2.2, dashed=True)

    # ── Pie (centrado) ──
    if data["ticket_legend"]:
        draw(data["ticket_legend"], size=6.5, align="center")
    if data["ticket_footer"]:
        y -= 0.6 * mm
        draw(data["ticket_footer"], size=8, bold=True, align="center")

    y -= 2 * mm
    draw("BIMABA™ - SARA POS", size=5.5, align="center")


# ──────────────────────────────────────────────────────────
# Impresión directa por GDI en Windows (sin PDF, sin visores)
# ──────────────────────────────────────────────────────────

def _print_windows_gdi(data, printer_name):
    """
    Dibuja el ticket directo sobre el Device Context de la impresora
    usando win32print/win32ui, indicando explícitamente el ancho de
    papel en décimas de milímetro. Esto evita depender de cualquier
    visor de PDF (que ignoraba el tamaño custom de página y causaba
    metros de papel en blanco antes del contenido).
    """
    import win32print
    import win32ui
    from win32con import MM_TWIPS

    target_printer = printer_name or win32print.GetDefaultPrinter()

    paper_width_mm = data["paper_width_mm"]
    # Twips: 1440 por pulgada, 1 pulgada = 25.4mm
    twips_per_mm = 1440 / 25.4
    page_width_twips = int(paper_width_mm * twips_per_mm)

    # Alto generoso (papel continuo); se recorta al avance real de impresión.
    page_height_mm = 90 + len(data["items"]) * 6
    page_height_twips = int(page_height_mm * twips_per_mm)

    hdc = win32ui.CreateDC()
    hdc.CreatePrinterDC(target_printer)
    hdc.SetMapMode(MM_TWIPS)

    hdc.StartDoc(f"SARA POS Ticket {data['ticket_id']:08d}")
    hdc.StartPage()

    _draw_ticket_gdi(hdc, page_width_twips, page_height_twips, data, twips_per_mm)

    hdc.EndPage()
    hdc.EndDoc()


def _draw_ticket_gdi(hdc, page_width, page_height, data, twips_per_mm):
    import win32ui

    def mmval(v):
        return int(v * twips_per_mm)

    margin = mmval(3.5)
    content_left = margin
    content_right = page_width - margin
    center = page_width // 2
    # En MM_TWIPS el origen está abajo a la izquierda con Y creciendo hacia
    # arriba; trabajamos con y_from_top y lo convertimos a negativo.
    y_from_top = mmval(6)

    def to_y(yt):
        return -yt

    def make_font(size_pt, bold=False):
        return win32ui.CreateFont({
            "name": "Arial",
            "height": -int(size_pt * twips_per_mm * 25.4 / 72 / 1),
            "weight": 700 if bold else 400,
        })

    # win32ui CreateFont height espera unidades lógicas (twips acá). Usamos
    # una conversión directa pt -> twips: 1pt = 20 twips.
    def font(size_pt, bold=False):
        return win32ui.CreateFont({
            "name": "Arial",
            "height": -int(size_pt * 20),
            "weight": 700 if bold else 400,
        })

    def text_width(hdc_, txt, fnt):
        hdc_.SelectObject(fnt)
        return hdc_.GetTextExtent(txt)[0]

    def draw(text, size=16, bold=False, align="center"):
        nonlocal y_from_top
        fnt = font(size, bold)
        hdc.SelectObject(fnt)
        w, h = hdc.GetTextExtent(text)
        if align == "center":
            x = center - w // 2
        elif align == "right":
            x = content_right - w
        else:
            x = content_left
        hdc.TextOut(x, to_y(y_from_top), text)
        y_from_top += int(h * 1.15)

    def hr(gap_before=mmval(1.2), gap_after=mmval(1.6)):
        nonlocal y_from_top
        y_from_top += gap_before
        pen = win32ui.CreatePen(0, 4, 0)
        old_pen = hdc.SelectObject(pen)
        hdc.MoveTo((content_left, to_y(y_from_top)))
        hdc.LineTo((content_right, to_y(y_from_top)))
        hdc.SelectObject(old_pen)
        y_from_top += gap_after

    # Tamaños en "puntos" aproximados, escalados a twips internamente.
    SZ_HEADER = 22
    SZ_SMALL  = 15
    SZ_BODY   = 16
    SZ_TOTAL  = 24

    draw(data["business_name"].upper(), size=SZ_HEADER, bold=True, align="center")
    if data["business_address"]:
        draw(data["business_address"], size=SZ_SMALL, align="center")
    if data["business_phone"]:
        draw(f"Tel: {data['business_phone']}", size=SZ_SMALL, align="center")
    if data["business_cuit"]:
        draw(f"CUIT: {data['business_cuit']}", size=SZ_SMALL, align="center")

    hr()

    draw("TICKET DE VENTA", size=SZ_BODY, bold=True, align="center")
    draw(f"N° {data['ticket_id']:08d}", size=SZ_BODY, align="left")
    draw(data["now"].strftime("%d/%m/%Y  %H:%M"), size=SZ_SMALL, align="left")
    draw(f"Forma de pago: {data['method_label']}", size=SZ_SMALL, align="left")

    hr()

    draw("DESCRIPCIÓN / CANT x PRECIO", size=SZ_SMALL, bold=True, align="left")
    hr(gap_before=mmval(0.4), gap_after=mmval(1.4))

    for item in data["items"]:
        name     = str(item["name"])[:28]
        qty      = int(item["quantity"])
        price    = float(item["price"])
        subtotal = qty * price

        draw(name, size=SZ_BODY, align="left")
        # Línea de cantidad x precio (izq) e importe (der) en la misma altura:
        fnt = font(SZ_SMALL, False)
        hdc.SelectObject(fnt)
        left_txt = f"{qty} x $ {price:,.0f}"
        hdc.TextOut(content_left + mmval(2), to_y(y_from_top), left_txt)
        w, h = hdc.GetTextExtent(f"$ {subtotal:,.0f}")
        hdc.TextOut(content_right - w, to_y(y_from_top), f"$ {subtotal:,.0f}")
        y_from_top += int(h * 1.3)

    hr(gap_before=mmval(0.8), gap_after=mmval(1.8))

    draw("TOTAL", size=SZ_TOTAL, bold=True, align="left")
    fnt = font(SZ_TOTAL, True)
    hdc.SelectObject(fnt)
    total_txt = f"$ {data['total']:,.0f}"
    w, h = hdc.GetTextExtent(total_txt)
    # Reescribimos en la misma línea del "TOTAL" (retrocedemos la altura usada)
    y_from_top -= int(h * 1.15)
    hdc.TextOut(content_right - w, to_y(y_from_top), total_txt)
    y_from_top += int(h * 1.15)

    hr(gap_before=mmval(0.5), gap_after=mmval(2.2))

    if data["ticket_legend"]:
        draw(data["ticket_legend"], size=13, align="center")
    if data["ticket_footer"]:
        draw(data["ticket_footer"], size=SZ_BODY, bold=True, align="center")

    draw("BIMABA™ - SARA POS", size=11, align="center")


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