from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QMessageBox,
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from app.database.database import SessionLocal
from app.models.settings_model import Setting


def get_setting(db, key, default=""):
    setting = db.query(Setting).filter(Setting.key == key).first()
    return setting.value if setting and setting.value else default


class TransferDialog(QDialog):

    def __init__(self, total, ticket_id, cart, payment_method, parent=None, on_confirm=None):
        super().__init__(parent)

        self.total = total
        self.ticket_id = ticket_id
        self.cart = cart
        self.payment_method = payment_method
        self.on_confirm = on_confirm
        self._registered_ticket_id = None
        self._registered_cart = None
        self.sale_confirmed = False

        self.setWindowTitle("Datos de pago")
        self.setFixedWidth(440)
        self.setMinimumHeight(300)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog { background-color: #F4F5F7; }
            QLabel { background-color: transparent; }
            QLabel#title { font-size: 18px; font-weight: bold; color: #1E293B; }
            QLabel#total_label { font-size: 13px; color: #64748B; }
            QLabel#total_value { font-size: 38px; font-weight: bold; color: #4A6A92; }
            QLabel#alias_title { font-size: 12px; color: #64748B; letter-spacing: 1px; }
            QLabel#alias_value { font-size: 20px; font-weight: bold; color: #1E293B; }
            QLabel#warning { font-size: 14px; color: #EF4444; font-weight: bold; }
            QFrame#card { background-color: white; border-radius: 16px; }
            QFrame#divider { background-color: #E2E8F0; max-height: 1px; }
            QPushButton#print_btn {
                background-color: #4A6A92; color: white; border: none;
                border-radius: 12px; padding: 16px; font-size: 16px; font-weight: bold;
            }
            QPushButton#print_btn:hover { background-color: #3D5A80; }
            QPushButton#cancel_btn {
                background-color: transparent; color: #94A3B8; border: none;
                font-size: 13px; padding: 8px;
            }
            QPushButton#cancel_btn:hover { color: #FF003D; }
        """)

        # Cargar configuración
        db = SessionLocal()
        try:
            self.alias = get_setting(db, "mp_alias", "")
            self.qr_path = get_setting(db, "payment_qr_path", "")
        finally:
            db.close()

        # Limpiar qr_path si no es válido
        if self.qr_path in ("QR no configurado", ""):
            self.qr_path = ""

        self.has_payment_data = bool(self.alias or self.qr_path)

        self.init_ui()

    def init_ui(self):

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(0)

        title_text = "Transferencia bancaria" if self.payment_method == "transfer" else "QR Mercado Pago"
        title = QLabel(title_text)
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        card_layout.addSpacing(16)

        subtitle = QLabel("Total a cobrar")
        subtitle.setObjectName("total_label")
        subtitle.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(4)

        total_label = QLabel(f"$ {int(self.total)}")
        total_label.setObjectName("total_value")
        total_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(total_label)

        card_layout.addSpacing(20)

        div = QFrame()
        div.setObjectName("divider")
        div.setFixedHeight(1)
        card_layout.addWidget(div)

        card_layout.addSpacing(20)

        if not self.has_payment_data:
            # Sin datos configurados
            warning = QLabel("⚠️  No hay métodos de pago configurados.\nAndá a Configuración → Métodos de pago.")
            warning.setObjectName("warning")
            warning.setAlignment(Qt.AlignCenter)
            warning.setWordWrap(True)
            card_layout.addWidget(warning)
            card_layout.addSpacing(20)

        else:
            # Mostrar alias si existe
            if self.alias:
                alias_title = QLabel("ALIAS / CBU")
                alias_title.setObjectName("alias_title")
                alias_title.setAlignment(Qt.AlignCenter)
                card_layout.addWidget(alias_title)

                card_layout.addSpacing(6)

                alias_val = QLabel(self.alias)
                alias_val.setObjectName("alias_value")
                alias_val.setAlignment(Qt.AlignCenter)
                card_layout.addWidget(alias_val)

                card_layout.addSpacing(20)

            # Mostrar QR si existe
            if self.qr_path:
                pixmap = QPixmap(self.qr_path)
                if not pixmap.isNull():
                    if self.alias:
                        div2 = QFrame()
                        div2.setObjectName("divider")
                        div2.setFixedHeight(1)
                        card_layout.addWidget(div2)
                        card_layout.addSpacing(20)

                    qr_label = QLabel()
                    qr_label.setAlignment(Qt.AlignCenter)
                    pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    qr_label.setPixmap(pixmap)
                    card_layout.addWidget(qr_label)
                    card_layout.addSpacing(12)

                    qr_hint = QLabel("Escaneá para pagar")
                    qr_hint.setObjectName("alias_title")
                    qr_hint.setAlignment(Qt.AlignCenter)
                    card_layout.addWidget(qr_hint)
                    card_layout.addSpacing(8)

        layout.addWidget(card)
        layout.addSpacing(4)

        # Botón imprimir solo si hay datos de pago
        if self.has_payment_data:
            print_btn = QPushButton("  Imprimir ticket")
            print_btn.setObjectName("print_btn")
            print_btn.setMinimumHeight(52)
            print_btn.clicked.connect(self.do_print_ticket)
            layout.addWidget(print_btn)

        cancel_btn = QPushButton("Volver a métodos de pago")
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.clicked.connect(self.do_cancel)
        layout.addWidget(cancel_btn, alignment=Qt.AlignCenter)

    def do_print_ticket(self):

        if self.on_confirm and self._registered_ticket_id is None:
            result = self.on_confirm()
            if result is None:
                return
            self._registered_ticket_id, self._registered_cart = result

        from app.printers.ticket_printer import print_ticket
        success, msg = print_ticket(
            self._registered_ticket_id,
            self._registered_cart,
            self.total,
            self.payment_method
        )

        box = QMessageBox(self)
        box.setWindowTitle("Imprimir")
        box.setText("Ticket enviado a imprimir" if success else f"Error: {msg}")
        box.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1E293B; font-size: 15px; font-weight: bold; min-width: 260px; }
            QPushButton {
                background-color: #4A6A92; color: white; border: none;
                border-radius: 10px; padding: 10px 20px; min-width: 80px;
                min-height: 32px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #3D5A80; }
        """)
        box.exec()

        self.sale_confirmed = True
        self.accept()

    def do_cancel(self):
        self.sale_confirmed = False
        self.reject()