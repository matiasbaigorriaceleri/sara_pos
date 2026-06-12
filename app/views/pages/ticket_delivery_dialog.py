"""
Diálogo de entrega de ticket — permite elegir entre imprimir o enviar por email.
Si elige email, pide los datos del cliente y envía el ticket.
"""

import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QWidget,
)
from PySide6.QtCore import Qt

from app.database.database import SessionLocal
from app.models.settings_model import Setting
from app.models.client_model import Client


def get_setting(db, key, default=""):
    s = db.query(Setting).filter(Setting.key == key).first()
    return s.value if s and s.value else default


class TicketDeliveryDialog(QDialog):
    """
    Paso 1: elegir Imprimir o Enviar por email.
    Paso 2 (si email): formulario con email obligatorio + datos opcionales.
    """

    def __init__(self, ticket_id, cart_snapshot, total, payment_method, parent=None):
        super().__init__(parent)
        self.ticket_id       = ticket_id
        self.cart_snapshot   = cart_snapshot
        self.total           = total
        self.payment_method  = payment_method
        self.delivery_method = None  # "print" | "email"

        self.setWindowTitle("Entrega de ticket")
        self.setMinimumWidth(460)
        self.setModal(True)
        self.setStyleSheet("background-color: white;")

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(28, 28, 28, 24)
        self._main_layout.setSpacing(16)

        self._show_step1()

    # ── Estilos comunes ───────────────────────────────

    def _btn_primary(self, text):
        btn = QPushButton(text)
        btn.setMinimumHeight(52)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #4A6A92; color: white;
                border: none; border-radius: 12px;
                font-size: 15px; font-weight: bold;
            }
            QPushButton:hover { background-color: #3D5A80; }
        """)
        return btn

    def _btn_secondary(self, text):
        btn = QPushButton(text)
        btn.setMinimumHeight(52)
        btn.setStyleSheet("""
            QPushButton {
                background-color: white; color: #4A6A92;
                border: 2px solid #4A6A92; border-radius: 12px;
                font-size: 15px; font-weight: bold;
            }
            QPushButton:hover { background-color: #EFF6FF; }
        """)
        return btn

    def _input(self, placeholder, required=False):
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder + (" *" if required else ""))
        inp.setMinimumHeight(48)
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

    def _clear_layout(self):
        while self._main_layout.count():
            item = self._main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ── Paso 1: elegir método ─────────────────────────

    def _show_step1(self):
        self._clear_layout()

        title = QLabel("¿Cómo entregamos el ticket?")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
        title.setAlignment(Qt.AlignCenter)
        self._main_layout.addWidget(title)

        total_lbl = QLabel(f"$ {int(self.total):,}")
        total_lbl.setStyleSheet("font-size: 32px; font-weight: bold; color: #4A6A92;")
        total_lbl.setAlignment(Qt.AlignCenter)
        self._main_layout.addWidget(total_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #E2E8F0;")
        self._main_layout.addWidget(sep)

        btn_print = self._btn_primary("🖨️   Imprimir ticket")
        btn_print.clicked.connect(self._choose_print)
        self._main_layout.addWidget(btn_print)

        btn_email = self._btn_secondary("✉️   Enviar por email")
        btn_email.clicked.connect(self._show_step2)
        self._main_layout.addWidget(btn_email)

        btn_none = QPushButton("Sin ticket")
        btn_none.setMinimumHeight(40)
        btn_none.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #94A3B8;
                border: none; font-size: 13px;
            }
            QPushButton:hover { color: #64748B; }
        """)
        btn_none.clicked.connect(self._choose_none)
        self._main_layout.addWidget(btn_none, alignment=Qt.AlignCenter)

    def _choose_print(self):
        self.delivery_method = "print"
        self.accept()

    def _choose_none(self):
        self.delivery_method = "none"
        self.accept()

    # ── Paso 2: formulario email ──────────────────────

    def _show_step2(self):
        self._clear_layout()

        title = QLabel("Enviar ticket por email")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
        title.setAlignment(Qt.AlignCenter)
        self._main_layout.addWidget(title)

        hint = QLabel("Solo el email es obligatorio. Los demás datos se guardan en Clientes.")
        hint.setStyleSheet("font-size: 12px; color: #64748B;")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignCenter)
        self._main_layout.addWidget(hint)

        self.email_input = self._input("Email del cliente", required=True)
        self._main_layout.addWidget(self.email_input)

        row = QHBoxLayout()
        self.nombre_input = self._input("Nombre")
        self.apellido_input = self._input("Apellido")
        row.addWidget(self.nombre_input)
        row.addWidget(self.apellido_input)
        self._main_layout.addLayout(row)

        self.celular_input = self._input("Celular (ej: 3516137769)")
        self._main_layout.addWidget(self.celular_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("font-size: 12px; color: #EF4444;")
        self._main_layout.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        btn_back = self._btn_secondary("← Volver")
        btn_back.clicked.connect(self._show_step1)
        btn_send = self._btn_primary("Enviar ticket")
        btn_send.clicked.connect(self._send_email)
        btn_row.addWidget(btn_back)
        btn_row.addWidget(btn_send)
        self._main_layout.addLayout(btn_row)

    def _send_email(self):
        email   = self.email_input.text().strip()
        nombre  = self.nombre_input.text().strip()
        apellido = self.apellido_input.text().strip()
        celular = self.celular_input.text().strip()

        # Validaciones
        if not email or "@" not in email or "." not in email.split("@")[-1]:
            self.error_label.setText("El email no es válido.")
            return

        if celular and not re.fullmatch(r"\d{10}", celular):
            self.error_label.setText("El celular debe tener exactamente 10 dígitos numéricos (ej: 3516137769).")
            return

        self.error_label.setText("Enviando...")

        # Guardar cliente si no existe
        self._save_client(email, nombre, apellido, celular)

        # Generar y enviar el PDF
        try:
            from app.printers.ticket_printer import generate_ticket_pdf
            pdf_path = generate_ticket_pdf(
                self.ticket_id, self.cart_snapshot,
                self.total, self.payment_method
            )
            self._send_smtp(email, pdf_path, nombre)
        except Exception as e:
            self.error_label.setText(f"Error al enviar: {str(e)}")
            return

        self.delivery_method = "email"
        self.accept()

    def _save_client(self, email, nombre, apellido, celular):
        """Guarda el cliente en la BD si no existe ya con ese email."""
        db = SessionLocal()
        try:
            existing = db.query(Client).filter(Client.email == email).first()
            if existing:
                return

            full_name = f"{nombre} {apellido}".strip().upper() or email.upper()

            # Generar número de cuenta
            last = db.query(Client).order_by(Client.id.desc()).first()
            num = 1
            if last and last.account_number:
                try:
                    num = int(last.account_number.replace("CC-", "")) + 1
                except Exception:
                    num = 1

            new_client = Client(
                account_number=f"CC-{str(num).zfill(5)}",
                name=full_name,
                phone=celular,
                email=email,
                address="",
                notes="Registrado desde punto de venta",
                discount=0,
                is_active=True
            )
            db.add(new_client)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    def _send_smtp(self, to_email, pdf_path, nombre):
        """Envía el ticket PDF por email usando la configuración SMTP de SARA."""
        db = SessionLocal()
        try:
            smtp_email    = get_setting(db, "smtp_email", "")
            smtp_password = get_setting(db, "smtp_password", "")
            smtp_host     = get_setting(db, "smtp_host", "smtp.gmail.com")
            smtp_port     = int(get_setting(db, "smtp_port", "587"))
            business_name = get_setting(db, "business_name", "SARA POS")
        finally:
            db.close()

        if not smtp_email or not smtp_password:
            raise Exception("Configurá el email en Configuración → Email antes de enviar.")

        saludo = f"Hola {nombre}," if nombre else "Hola,"

        msg = MIMEMultipart()
        msg["From"]    = smtp_email
        msg["To"]      = to_email
        msg["Subject"] = f"Tu ticket de compra — {business_name}"

        body = (
            f"{saludo}\n\n"
            f"Adjuntamos el comprobante de tu compra en {business_name}.\n\n"
            f"Total: $ {int(self.total):,}\n"
            f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
            f"¡Gracias por tu compra!\n\n"
            f"— {business_name}"
        )
        msg.attach(MIMEText(body, "plain"))

        # Adjuntar PDF
        import os
        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename=ticket_{self.ticket_id:05d}.pdf"
        )
        msg.attach(part)

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, to_email, msg.as_string())