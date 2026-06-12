import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import Qt

from app.database.database import SessionLocal
from app.models.settings_model import Setting
from app.models.client_model import Client


def get_setting(db, key, default=""):
    s = db.query(Setting).filter(Setting.key == key).first()
    return s.value if s and s.value else default


class TicketDeliveryDialog(QDialog):

    def __init__(self, ticket_id, cart_snapshot, total, payment_method, parent=None):
        super().__init__(parent)
        self.ticket_id      = ticket_id
        self.cart_snapshot  = cart_snapshot
        self.total          = total
        self.payment_method = payment_method
        self.delivery_method = None
        self._selected_client = None

        self.setWindowTitle("Entrega de ticket")
        self.setMinimumWidth(480)
        self.setModal(True)
        self.setStyleSheet("background-color: white;")

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(28, 28, 28, 24)
        self._main_layout.setSpacing(14)

        self._show_step1()

    # ── Helpers de estilo ─────────────────────────────

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

    def _btn_cancel(self, text="Cancelar venta"):
        btn = QPushButton(text)
        btn.setMinimumHeight(40)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #EF4444;
                border: none; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { color: #DC2626; }
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
            elif item.layout():
                self._clear_sublayout(item.layout())

    def _clear_sublayout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
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

    # ── Paso 2: buscar o cargar cliente ───────────────

    def _show_step2(self):
        self._clear_layout()
        self._selected_client = None

        title = QLabel("Enviar ticket por email")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
        title.setAlignment(Qt.AlignCenter)
        self._main_layout.addWidget(title)

        # Buscador
        search_label = QLabel("Buscar cliente existente:")
        search_label.setStyleSheet("font-size: 13px; color: #64748B;")
        self._main_layout.addWidget(search_label)

        search_row = QHBoxLayout()
        self._search_input = self._input("Nombre o email del cliente...")
        self._search_input.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self._search_input)
        self._main_layout.addLayout(search_row)

        # Lista de resultados
        self._results_list = QListWidget()
        self._results_list.setMaximumHeight(120)
        self._results_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #B8C4D0;
                border-radius: 8px;
                font-size: 13px;
                color: #1E293B;
                background: white;
            }
            QListWidget::item:selected {
                background-color: #D8E6F5;
                color: #1E293B;
            }
            QListWidget::item:hover {
                background-color: #EFF6FF;
            }
        """)
        self._results_list.hide()
        self._results_list.itemClicked.connect(self._on_client_selected)
        self._main_layout.addWidget(self._results_list)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #E2E8F0;")
        self._main_layout.addWidget(sep)

        # Formulario
        form_label = QLabel("Datos del cliente:")
        form_label.setStyleSheet("font-size: 13px; color: #64748B;")
        self._main_layout.addWidget(form_label)

        self.email_input = self._input("Email *", required=False)
        self._main_layout.addWidget(self.email_input)

        name_row = QHBoxLayout()
        self.nombre_input = self._input("Nombre")
        self.apellido_input = self._input("Apellido")
        name_row.addWidget(self.nombre_input)
        name_row.addWidget(self.apellido_input)
        self._main_layout.addLayout(name_row)

        self.celular_input = self._input("Celular (ej: 3516137769)")
        self._main_layout.addWidget(self.celular_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("font-size: 12px; color: #EF4444;")
        self._main_layout.addWidget(self.error_label)

        # Botones
        btn_row = QHBoxLayout()
        btn_back = self._btn_secondary("← Volver")
        btn_back.clicked.connect(self._show_step1)
        btn_send = self._btn_primary("Enviar ticket")
        btn_send.clicked.connect(self._send_email)
        btn_row.addWidget(btn_back)
        btn_row.addWidget(btn_send)
        self._main_layout.addLayout(btn_row)

        btn_cancel = self._btn_cancel("✕  Cancelar venta")
        btn_cancel.clicked.connect(self.reject)
        self._main_layout.addWidget(btn_cancel, alignment=Qt.AlignCenter)

    def _on_search_changed(self, text):
        query = text.strip().upper()
        self._results_list.clear()
        self._selected_client = None

        if len(query) < 2:
            self._results_list.hide()
            return

        db = SessionLocal()
        try:
            clients = db.query(Client).filter(
                Client.is_active == True
            ).all()
            matches = [
                c for c in clients
                if query in (c.name or "").upper()
                or query in (c.email or "").upper()
            ]
        finally:
            db.close()

        if not matches:
            self._results_list.hide()
            return

        for c in matches[:8]:
            label = f"{c.name}  —  {c.email or 'sin email'}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, {
                "id": c.id,
                "name": c.name or "",
                "email": c.email or "",
                "phone": c.phone or "",
            })
            self._results_list.addItem(item)

        self._results_list.show()

    def _on_client_selected(self, item):
        data = item.data(Qt.UserRole)
        self._selected_client = data

        # Separar nombre y apellido
        parts = (data["name"] or "").split(" ", 1)
        nombre   = parts[0] if parts else ""
        apellido = parts[1] if len(parts) > 1 else ""

        self.email_input.setText(data["email"])
        self.nombre_input.setText(nombre)
        self.apellido_input.setText(apellido)
        self.celular_input.setText(data["phone"])

        self._results_list.hide()
        self._search_input.clear()
        self.error_label.setText(f"✓ Cliente seleccionado: {data['name']}")
        self.error_label.setStyleSheet("font-size: 12px; color: #16A34A;")

    # ── Envío ─────────────────────────────────────────

    def _send_email(self):
        email    = self.email_input.text().strip()
        nombre   = self.nombre_input.text().strip()
        apellido = self.apellido_input.text().strip()
        celular  = self.celular_input.text().strip()

        if not email or "@" not in email or "." not in email.split("@")[-1]:
            self.error_label.setStyleSheet("font-size: 12px; color: #EF4444;")
            self.error_label.setText("El email no es válido.")
            return

        if celular and not re.fullmatch(r"\d{10}", celular):
            self.error_label.setStyleSheet("font-size: 12px; color: #EF4444;")
            self.error_label.setText("El celular debe tener 10 dígitos numéricos (ej: 3516137769).")
            return

        self.error_label.setStyleSheet("font-size: 12px; color: #64748B;")
        self.error_label.setText("Enviando...")

        # Guardar o actualizar cliente
        if not self._selected_client:
            self._save_new_client(email, nombre, apellido, celular)

        try:
            from app.printers.ticket_printer import generate_ticket_pdf
            pdf_path = generate_ticket_pdf(
                self.ticket_id, self.cart_snapshot,
                self.total, self.payment_method
            )
            self._send_smtp(email, pdf_path, nombre)
        except Exception as e:
            self.error_label.setStyleSheet("font-size: 12px; color: #EF4444;")
            self.error_label.setText(f"Error al enviar: {str(e)}")
            return

        self.delivery_method = "email"
        self.accept()

    def _save_new_client(self, email, nombre, apellido, celular):
        db = SessionLocal()
        try:
            existing = db.query(Client).filter(Client.email == email).first()
            if existing:
                return

            full_name = f"{nombre} {apellido}".strip().upper() or email.upper()

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
            raise Exception("Configurá el email en Configuración → Email.")

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