"""
SARA POS — Wizard de configuración inicial
==========================================
Se muestra cada vez que se abre la app, mientras "business_name" esté vacío
y el usuario no haya tildado "No molestar más".
Pasos: Bienvenida → Datos negocio → Impresora → Ticket → Listo
"""

import subprocess
import platform

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QFrame,
    QWidget, QStackedWidget, QCheckBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from app.database.database import SessionLocal
from app.models.settings_model import Setting
from app.assets.themes.theme import PRIMARY_COLOR


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
    """
    Devuelve True si el wizard debe mostrarse: el negocio no está
    configurado todavía Y el usuario no pidió que no se le moleste más.
    """
    db = SessionLocal()
    try:
        s_name = db.query(Setting).filter(Setting.key == "business_name").first()
        business_missing = not s_name or not (s_name.value or "").strip()

        s_dont_ask = db.query(Setting).filter(Setting.key == "setup_dont_ask_again").first()
        dont_ask = bool(s_dont_ask and (s_dont_ask.value or "").strip() == "1")

        return business_missing and not dont_ask
    finally:
        db.close()


class SetupWizard(QDialog):

    TOTAL_STEPS = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración inicial — SARA POS")
        self.setMinimumWidth(580)
        self.setMinimumHeight(600)
        self.setModal(True)
        self.setStyleSheet("background-color: white;")
        # El wizard ahora SÍ se puede cerrar (botón X visible) y posponer.

        self._step = 0

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barra de progreso
        self._progress_bar = QWidget()
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setStyleSheet("background-color: #E2E8F0;")
        main_layout.addWidget(self._progress_bar)

        self._progress_fill = QWidget(self._progress_bar)
        self._progress_fill.setFixedHeight(6)
        self._progress_fill.setStyleSheet(f"background-color: {PRIMARY_COLOR};")
        self._progress_fill.setFixedWidth(0)

        self._stack = QStackedWidget()
        main_layout.addWidget(self._stack)

        # Checkbox "No molestar más" — visible en todos los pasos
        dont_ask_frame = QFrame()
        dont_ask_layout = QHBoxLayout(dont_ask_frame)
        dont_ask_layout.setContentsMargins(28, 4, 28, 4)

        self._chk_dont_ask = QCheckBox("No preguntar más (podrás completar estos datos luego, manualmente, desde Configuración)")
        self._chk_dont_ask.setStyleSheet("font-size: 12px; color: #64748B;")
        dont_ask_layout.addWidget(self._chk_dont_ask)
        dont_ask_layout.addStretch()
        main_layout.addWidget(dont_ask_frame)

        # Navegación
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
            QPushButton { background-color: transparent; color: #94A3B8; border: none; font-size: 13px; }
            QPushButton:hover { color: #64748B; }
        """)
        self._btn_skip.clicked.connect(self._skip_step)
        nav_layout.addWidget(self._btn_skip)

        self._btn_next = QPushButton("Siguiente →")
        self._btn_next.setFixedHeight(42)
        self._btn_next.setFixedWidth(160)
        self._btn_next.setStyleSheet(f"""
            QPushButton {{ background-color: {PRIMARY_COLOR}; color: white; border: none; border-radius: 10px; font-size: 14px; font-weight: bold; }}
            QPushButton:hover {{ background-color: #3D5A80; }}
        """)
        self._btn_next.clicked.connect(self._next_step)
        nav_layout.addWidget(self._btn_next)

        main_layout.addWidget(nav_frame)

        self._build_step0()
        self._build_step1()
        self._build_step2()
        self._build_step3()
        self._build_step4()

        self._update_nav()

    # ── Helpers UI ────────────────────────────────────

    def _page(self, title, subtitle=None):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 28, 40, 20)
        layout.setSpacing(12)

        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {PRIMARY_COLOR};")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet("font-size: 13px; color: #64748B;")
            sub.setWordWrap(True)
            layout.addWidget(sub)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #E2E8F0;")
        layout.addWidget(sep)

        return widget, layout

    def _input(self, placeholder):
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setMinimumHeight(48)
        inp.setStyleSheet("""
            QLineEdit {
                background-color: white; border: 2px solid #B8C4D0;
                border-radius: 10px; padding: 8px 14px;
                font-size: 14px; color: #1E293B;
            }
            QLineEdit:focus { border: 2px solid #4A6A92; }
        """)
        return inp

    def _combo(self, items):
        c = QComboBox()
        c.addItems(items)
        c.setMinimumHeight(48)
        c.setStyleSheet("""
            QComboBox {
                background-color: white; border: 2px solid #B8C4D0;
                border-radius: 10px; padding: 8px 14px;
                font-size: 14px; color: #1E293B;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: white; color: #1E293B; selection-background-color: #D8E6F5; }
        """)
        return c

    def _error_label(self):
        lbl = QLabel("")
        lbl.setStyleSheet("font-size: 12px; color: #EF4444;")
        lbl.setWordWrap(True)
        return lbl

    def _get_logo(self, size=110):
        import sys, os
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignCenter)
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        else:
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        for path in [
            os.path.join(base, "app", "utils", "SARA.png"),
            os.path.join(base, "app", "assets", "sara_pos_icon.png"),
        ]:
            if os.path.exists(path):
                px = QPixmap(path).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                lbl.setPixmap(px)
                break
        return lbl

    # ── Paso 0: Bienvenida ────────────────────────────

    def _build_step0(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 32, 40, 20)
        layout.setSpacing(14)
        layout.addStretch()
        layout.addWidget(self._get_logo(110))

        title = QLabel("Bienvenido a SARA POS")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {PRIMARY_COLOR};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Antes de comenzar, configuremos tu sistema.\nEsto solo toma 2 minutos.")
        subtitle.setStyleSheet("font-size: 14px; color: #64748B;")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        info = QLabel(
            "  📋  Datos de tu negocio\n"
            "  🖨️   Impresora\n"
            "  🎫  Datos del ticket"
        )
        info.setStyleSheet(
            "font-size: 13px; color: #1E293B; background-color: #F0F7FF; "
            "border-radius: 10px; padding: 14px;"
        )
        layout.addWidget(info)
        layout.addStretch()
        self._stack.addWidget(widget)

    # ── Paso 1: Datos del negocio ─────────────────────

    def _build_step1(self):
        widget, layout = self._page(
            "📋  Datos de tu negocio",
            "El nombre es obligatorio y aparecerá en los tickets.",
        )

        self._biz_name  = self._input("Nombre del negocio *")
        self._biz_cuit  = self._input("CUIT / CUIL (sin guiones)")
        self._biz_addr  = self._input("Dirección")
        self._biz_phone = self._input("Teléfono del negocio")

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
            "Seleccioná la impresora y el tamaño del papel."
        )

        lbl1 = QLabel("Impresora:")
        lbl1.setStyleSheet("font-size: 13px; color: #64748B;")
        layout.addWidget(lbl1)

        self._printer_combo = self._combo(self._get_printers())
        layout.addWidget(self._printer_combo)

        btn_refresh = QPushButton("🔄  Actualizar lista")
        btn_refresh.setFixedHeight(40)
        btn_refresh.setStyleSheet("""
            QPushButton { background-color: #F1F5F9; color: #4A6A92; border: 1px solid #B8C4D0; border-radius: 8px; font-size: 13px; font-weight: bold; }
            QPushButton:hover { background-color: #D8E6F5; }
        """)
        btn_refresh.clicked.connect(self._refresh_printers)
        layout.addWidget(btn_refresh)

        lbl2 = QLabel("Tamaño del papel:")
        lbl2.setStyleSheet("font-size: 13px; color: #64748B;")
        layout.addWidget(lbl2)

        self._size_combo = self._combo(["80mm", "58mm"])
        layout.addWidget(self._size_combo)

        layout.addStretch()
        self._stack.addWidget(widget)

    # ── Paso 3: Ticket ────────────────────────────────

    def _build_step3(self):
        widget, layout = self._page(
            "🎫  Datos del ticket",
            "Textos que aparecerán en cada comprobante de venta."
        )

        lbl1 = QLabel("Leyenda (parte superior):")
        lbl1.setStyleSheet("font-size: 13px; color: #64748B;")
        layout.addWidget(lbl1)

        self._ticket_legend = self._input("Comprobante no válido como factura")
        self._ticket_legend.setText("Comprobante no válido como factura")
        layout.addWidget(self._ticket_legend)

        lbl2 = QLabel("Pie del ticket:")
        lbl2.setStyleSheet("font-size: 13px; color: #64748B;")
        layout.addWidget(lbl2)

        self._ticket_footer = self._input("Gracias por su compra")
        self._ticket_footer.setText("Gracias por su compra")
        layout.addWidget(self._ticket_footer)

        layout.addStretch()
        self._stack.addWidget(widget)

    # ── Paso 4: Listo ─────────────────────────────────

    def _build_step4(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 32, 40, 20)
        layout.setSpacing(14)
        layout.addStretch()
        layout.addWidget(self._get_logo(90))

        title = QLabel("¡Todo listo!")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {PRIMARY_COLOR};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(
            "Tu sistema está configurado y listo para usar.\n"
            "Podés modificar cualquier dato desde Configuración."
        )
        subtitle.setStyleSheet("font-size: 14px; color: #64748B;")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        bimaba = QLabel("Desarrollado por BIMABA™")
        bimaba.setStyleSheet("font-size: 11px; color: #94A3B8;")
        bimaba.setAlignment(Qt.AlignCenter)
        layout.addWidget(bimaba)

        layout.addStretch()
        self._stack.addWidget(widget)

    # ── Navegación ────────────────────────────────────

    def _update_nav(self):
        total_width = self.width() or 580
        fill = int((self._step / (self.TOTAL_STEPS - 1)) * total_width)
        self._progress_fill.setFixedWidth(fill)
        self._step_label.setText(f"Paso {self._step + 1} de {self.TOTAL_STEPS}")

        if self._step == self.TOTAL_STEPS - 1:
            self._btn_next.setText("¡Comenzar!")
            self._btn_skip.hide()
        elif self._step == 0:
            self._btn_next.setText("Comenzar →")
            self._btn_skip.hide()
        elif self._step in (2, 3):
            self._btn_next.setText("Siguiente →")
            self._btn_skip.show()
        else:
            self._btn_next.setText("Siguiente →")
            self._btn_skip.hide()

        self._stack.setCurrentIndex(self._step)

    def _next_step(self):
        if self._chk_dont_ask.isChecked():
            self._finish()
            return

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
            self._finish()
            return

        self._step += 1
        self._update_nav()

    def _skip_step(self):
        if self._chk_dont_ask.isChecked():
            self._finish()
            return
        self._step += 1
        self._update_nav()

    def _finish(self):
        self._save_dont_ask_preference()
        self.accept()

    def _save_dont_ask_preference(self):
        if self._chk_dont_ask.isChecked():
            _save_settings({"setup_dont_ask_again": "1"})

    # ── Guardar ───────────────────────────────────────

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
            _save_settings({"printer_name": printer, "printer_size": size})

    def _save_step3(self):
        _save_settings({
            "ticket_legend": self._ticket_legend.text().strip(),
            "ticket_footer": self._ticket_footer.text().strip(),
        })

    # ── Helpers ───────────────────────────────────────

    def _get_printers(self):
        printers = []
        try:
            if platform.system() == "Windows":
                result = subprocess.run(["wmic", "printer", "get", "name"], capture_output=True, text=True)
                for line in result.stdout.strip().splitlines()[1:]:
                    name = line.strip()
                    if name:
                        printers.append(name)
            else:
                result = subprocess.run(["lpstat", "-a"], capture_output=True, text=True)
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.TOTAL_STEPS > 1 and self._step > 0:
            fill = int((self._step / (self.TOTAL_STEPS - 1)) * self.width())
            self._progress_fill.setFixedWidth(fill)

    def closeEvent(self, event):
        # Ahora SÍ se puede cerrar el wizard en cualquier momento (X, Esc,
        # Alt+F4). Si no tildó "No molestar más", reaparecerá la próxima
        # vez que se abra SARA mientras el negocio no esté configurado.
        self._save_dont_ask_preference()
        event.accept()