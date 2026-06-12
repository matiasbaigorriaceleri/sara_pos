"""
SARA POS — Wizard de configuración inicial
==========================================
Se muestra la primera vez que se abre la app (cuando business_name está vacío).
Guía al usuario por los pasos básicos de configuración.
"""

import subprocess
import platform

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QFrame,
    QWidget, QStackedWidget,
)
from PySide6.QtCore import Qt

from app.database.database import SessionLocal
from app.models.settings_model import Setting
from app.assets.themes.theme import PRIMARY_COLOR


# ── Helpers ───────────────────────────────────────────

def _save_settings(data: dict):
    db = SessionLocal()
    try:
        for key, value in data.items():
            s = db.query(Setting).filter(Setting.key == key).first()
            if s:
                s.value = value
            else:
                db.add(Setting(key=key, value=value))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def is_first_run() -> bool:
    """Devuelve True si es la primera vez que se abre SARA (business_name vacío)."""
    db = SessionLocal()
    try:
        s = db.query(Setting).filter(Setting.key == "business_name").first()
        return not s or not (s.value or "").strip()
    finally:
        db.close()


SMTP_PROVIDERS = {
    "Gmail":              ("smtp.gmail.com",       "587"),
    "Outlook / Hotmail":  ("smtp.office365.com",   "587"),
    "Yahoo":              ("smtp.mail.yahoo.com",   "587"),
    "Otro (manual)":      ("",                      "587"),
}


class SetupWizard(QDialog):

    TOTAL_STEPS = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración inicial — SARA POS")
        self.setMinimumWidth(560)
        self.setMinimumHeight(520)
        self.setModal(True)
        self.setStyleSheet("background-color: white;")
        # No permitir cerrar con la X
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)

        self._step = 0

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Barra de progreso superior ────────────────
        self._progress_bar = QWidget()
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setStyleSheet(f"background-color: #E2E8F0;")
        main_layout.addWidget(self._progress_bar)

        self._progress_fill = QWidget(self._progress_bar)
        self._progress_fill.setFixedHeight(6)
        self._progress_fill.setStyleSheet(f"background-color: {PRIMARY_COLOR};")
        self._progress_fill.setFixedWidth(0)

        # ── Contenido ─────────────────────────────────
        self._stack = QStackedWidget()
        main_layout.addWidget(self._stack)

        # ── Botones navegación ────────────────────────
        nav_frame = QFrame()
        nav_frame.setStyleSheet("background-color: #F8FAFC; border-top: 1px solid #E2E8F0;")
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(28, 16, 28, 16)
        nav_layout.setSpacing(12)

        self._step_label = QLabel("Paso 1 de 5")
        self._step_label.setStyleSheet("font-size: 12px; color: #94A3B8;")
        nav_layout.addWidget(self._step_label)
        nav_layout.addStretch()

        self._btn_skip = QPushButton("Configurar después")
        self._btn_skip.setFixedHeight(42)
        self._btn_skip.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #94A3B8;
                border: none; font-size: 13px;
            }
            QPushButton:hover { color: #64748B; }
        """)
        self._btn_skip.clicked.connect(self._skip_step)
        nav_layout.addWidget(self._btn_skip)

        self._btn_next = QPushButton("Siguiente →")
        self._btn_next.setFixedHeight(42)
        self._btn_next.setFixedWidth(160)
        self._btn_next.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY_COLOR}; color: white;
                border: none; border-radius: 10px;
                font-size: 14px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #3D5A80; }}
        """)
        self._btn_next.clicked.connect(self._next_step)
        nav_layout.addWidget(self._btn_next)

        main_layout.addWidget(nav_frame)

        # ── Construir pasos ───────────────────────────
        self._build_step0()  # Bienvenida
        self._build_step1()  # Datos del negocio
        self._build_step2()  # Impresora
        self._build_step3()  # Ticket
        self._build_step4()  # Listo

        self._update_nav()

    # ── Helpers UI ────────────────────────────────────

    def _page(self, title, subtitle=None, skippable=True):
        """Crea un QWidget con layout estándar para cada paso."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 32, 40, 24)
        layout.setSpacing(16)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {PRIMARY_COLOR};")
        lbl_title.setWordWrap(True)
        layout.addWidget(lbl_title)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setStyleSheet("font-size: 14px; color: #64748B;")
            lbl_sub.setWordWrap(True)
            layout.addWidget(lbl_sub)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #E2E8F0; margin-bottom: 4px;")
        layout.addWidget(sep)

        return widget, layout

    def _input(self, placeholder, required=False):
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder + (" *" if required else ""))
        inp.setMinimumHeight(50)
        inp.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #B8C4D0;
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 14px;
                color: #1E293B;
            }
            QLineEdit:focus { border: 2px solid #4A6A92; }
        """)
        return inp

    def _combo(self, items):
        c = QComboBox()
        c.addItems(items)
        c.setMinimumHeight(50)
        c.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 2px solid #B8C4D0;
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 14px;
                color: #1E293B;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #1E293B;
                selection-background-color: #D8E6F5;
            }
        """)
        return c

    def _error_label(self):
        lbl = QLabel("")
        lbl.setStyleSheet("font-size: 12px; color: #EF4444;")
        lbl.setWordWrap(True)
        return lbl

    # ── Paso 0: Bienvenida ────────────────────────────

    def _build_step0(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 24)
        layout.setSpacing(16)
        layout.addStretch()

        # ── Logo SARA POS ─────────────────────────────
        from PySide6.QtGui import QPixmap
        from PySide6.QtWidgets import QLabel as _QLabel
        import sys, os

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)

        # Buscar el logo
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        else:
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        logo_path = os.path.join(base, "app", "utils", "SARA.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(base, "app", "assets", "sara_pos_icon.png")

        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("SARA")
            logo_label.setStyleSheet(f"font-size: 48px; font-weight: bold; color: {PRIMARY_COLOR};")

        layout.addWidget(logo_label)

        title = QLabel("Bienvenido a SARA POS")
        title.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {PRIMARY_COLOR};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Antes de comenzar, configuremos tu negocio.\nEsto solo toma 2 minutos.")
        subtitle.setStyleSheet("font-size: 15px; color: #64748B;")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        steps_info = QLabel(
            "Vamos a configurar:\n"
            "  📋  Datos de tu negocio\n"
            "  🖨️   Impresora\n"
            "  🎫  Datos del ticket"
        )
        steps_info.setStyleSheet(
            "font-size: 13px; color: #1E293B; "
            "background-color: #F0F7FF; border-radius: 10px; "
            "padding: 16px;"
        )
        steps_info.setAlignment(Qt.AlignLeft)
        layout.addWidget(steps_info)

        layout.addStretch()
        self._stack.addWidget(widget)

    # ── Paso 1: Datos del negocio ─────────────────────

    def _build_step1(self):
        widget, layout = self._page(
            "📋  Datos de tu negocio",
            "El nombre es obligatorio y aparecerá en los tickets.",
            skippable=False
        )

        self._biz_name   = self._input("Nombre del negocio", required=True)
        self._biz_cuit   = self._input("CUIT / CUIL (sin guiones)")
        self._biz_addr   = self._input("Dirección")
        self._biz_phone  = self._input("Teléfono")

        layout.addWidget(self._biz_name)
        layout.addWidget(self._biz_cuit)
        layout.addWidget(self._biz_addr)
        layout.addWidget(self._biz_phone)

        self._step1_error = self._error_label()
        layout.addWidget(self._step1_error)
        layout.addStretch()

        self._stack.addWidget(widget)

    # ── Paso 2: Impresora ─────────────────────────────

    def _build_step2(self):
        widget, layout = self._page(
            "🖨️   Impresora",
            "Seleccioná la impresora y el tamaño del papel para los tickets."
        )

        printer_label = QLabel("Impresora:")
        printer_label.setStyleSheet("font-size: 13px; color: #64748B;")
        layout.addWidget(printer_label)

        self._printer_combo = self._combo(self._get_printers())
        layout.addWidget(self._printer_combo)

        btn_refresh = QPushButton("🔄  Actualizar lista")
        btn_refresh.setFixedHeight(40)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9; color: #4A6A92;
                border: 1px solid #B8C4D0; border-radius: 8px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #D8E6F5; }
        """)
        btn_refresh.clicked.connect(self._refresh_printers)
        layout.addWidget(btn_refresh)

        size_label = QLabel("Tamaño del papel:")
        size_label.setStyleSheet("font-size: 13px; color: #64748B;")
        layout.addWidget(size_label)

        self._size_combo = self._combo(["80mm", "58mm"])
        layout.addWidget(self._size_combo)

        layout.addStretch()
        self._stack.addWidget(widget)

    def _get_printers(self):
        printers = []
        try:
            if platform.system() == "Windows":
                import subprocess
                result = subprocess.run(
                    ["wmic", "printer", "get", "name"],
                    capture_output=True, text=True
                )
                for line in result.stdout.strip().splitlines()[1:]:
                    name = line.strip()
                    if name:
                        printers.append(name)
            else:
                result = subprocess.run(
                    ["lpstat", "-a"], capture_output=True, text=True
                )
                for line in result.stdout.strip().splitlines():
                    name = line.split()[0]
                    if name:
                        printers.append(name)
        except Exception:
            pass
        return printers if printers else ["Sin impresoras detectadas"]

    def _refresh_printers(self):
        self._printer_combo.clear()
        self._printer_combo.addItems(self._get_printers())

    # ── Paso 3: Ticket ────────────────────────────────

    def _build_step3(self):
        widget, layout = self._page(
            "🎫  Datos del ticket",
            "Estos textos aparecerán en cada comprobante de venta."
        )

        legend_label = QLabel("Leyenda (parte superior del ticket):")
        legend_label.setStyleSheet("font-size: 13px; color: #64748B;")
        layout.addWidget(legend_label)

        self._ticket_legend = self._input("Ej: Comprobante no válido como factura")
        self._ticket_legend.setText("Comprobante no válido como factura")
        layout.addWidget(self._ticket_legend)

        footer_label = QLabel("Pie del ticket:")
        footer_label.setStyleSheet("font-size: 13px; color: #64748B;")
        layout.addWidget(footer_label)

        self._ticket_footer = self._input("Ej: Gracias por su compra")
        self._ticket_footer.setText("Gracias por su compra")
        layout.addWidget(self._ticket_footer)

        layout.addStretch()
        self._stack.addWidget(widget)

    # ── Paso 4: Listo ─────────────────────────────────

    def _build_step4(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 24)
        layout.setSpacing(16)
        layout.addStretch()

        # Logo
        from PySide6.QtGui import QPixmap
        import sys, os
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)

        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        else:
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        logo_path = os.path.join(base, "app", "utils", "SARA.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(base, "app", "assets", "sara_pos_icon.png")

        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        layout.addWidget(logo_label)

        title = QLabel("¡Todo listo!")
        title.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {PRIMARY_COLOR};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(
            "Tu negocio está configurado.\n"
            "Podés modificar cualquier dato en cualquier momento\n"
            "desde Configuración."
        )
        subtitle.setStyleSheet("font-size: 15px; color: #64748B;")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        bimaba = QLabel("Desarrollado por BIMABA™")
        bimaba.setStyleSheet("font-size: 12px; color: #94A3B8;")
        bimaba.setAlignment(Qt.AlignCenter)
        layout.addWidget(bimaba)

        layout.addStretch()
        self._stack.addWidget(widget)

    # ── Navegación ────────────────────────────────────

    def _update_nav(self):
        # Progreso
        total_width = self.width() or 560
        fill = int((self._step / (self.TOTAL_STEPS - 1)) * total_width)
        self._progress_fill.setFixedWidth(fill)

        self._step_label.setText(f"Paso {self._step + 1} de {self.TOTAL_STEPS}")

        # Último paso
        if self._step == self.TOTAL_STEPS - 1:
            self._btn_next.setText("¡Comenzar!")
            self._btn_skip.hide()
        elif self._step == 0:
            self._btn_next.setText("Comenzar →")
            self._btn_skip.hide()
        else:
            self._btn_next.setText("Siguiente →")
            self._btn_skip.show() if self._step in (2, 3) else self._btn_skip.hide()

        self._stack.setCurrentIndex(self._step)

    def _next_step(self):
        # Validar paso actual antes de avanzar
        if self._step == 1:
            if not self._biz_name.text().strip():
                self._step1_error.setText("El nombre del negocio es obligatorio.")
                return
            self._step1_error.setText("")
            self._save_step1()

        elif self._step == 2:
            self._save_step2()

        elif self._step == 3:
            self._save_step3()

        elif self._step == self.TOTAL_STEPS - 1:
            self.accept()
            return

        self._step += 1
        self._update_nav()

    def _skip_step(self):
        """Saltar pasos opcionales (impresora y ticket)."""
        self._step += 1
        self._update_nav()

    # ── Guardar datos ─────────────────────────────────

    def _save_step1(self):
        _save_settings({
            "business_name":    self._biz_name.text().strip(),
            "business_cuit":    self._biz_cuit.text().strip(),
            "business_address": self._biz_addr.text().strip(),
            "business_phone":   self._biz_phone.text().strip(),
        })

    def _save_step2(self):
        printer = self._printer_combo.currentText()
        size    = self._size_combo.currentText()
        if printer != "Sin impresoras detectadas":
            _save_settings({
                "printer_name": printer,
                "printer_size": size,
            })

    def _save_step3(self):
        _save_settings({
            "ticket_legend": self._ticket_legend.text().strip(),
            "ticket_footer": self._ticket_footer.text().strip(),
        })

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.TOTAL_STEPS > 1:
            fill = int((self._step / (self.TOTAL_STEPS - 1)) * self.width())
            self._progress_fill.setFixedWidth(fill)