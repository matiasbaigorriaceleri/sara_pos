from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from app.database.database import SessionLocal
from app.models.settings_model import Setting


def get_setting(db, key, default=""):
    setting = db.query(Setting).filter(
        Setting.key == key
    ).first()
    return setting.value if setting and setting.value else default


class TransferDialog(QDialog):

    def __init__(self, total, ticket_id, cart, payment_method, parent=None):
        super().__init__(parent)

        self.total = total
        self.ticket_id = ticket_id
        self.cart = cart
        self.payment_method = payment_method

        self.setWindowTitle("Datos de pago")
        self.setFixedSize(480, 520)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog {
                background-color: #F4F5F7;
            }
            QLabel#title {
                font-size: 20px;
                font-weight: bold;
                color: #1E293B;
            }
            QLabel#total {
                font-size: 32px;
                font-weight: bold;
                color: #4A6A92;
            }
            QLabel#subtitle {
                font-size: 14px;
                color: #64748B;
            }
            QLabel#alias {
                font-size: 18px;
                font-weight: bold;
                color: #1E293B;
                background-color: white;
                border: 2px solid #B8C4D0;
                border-radius: 10px;
                padding: 12px;
            }
            QPushButton#print_btn {
                background-color: #4A6A92;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 16px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#print_btn:hover {
                background-color: #3D5A80;
            }
            QPushButton#cancel_btn {
                background-color: transparent;
                color: #64748B;
                border: none;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton#cancel_btn:hover {
                color: #FF003D;
            }
        """)

        self.init_ui()

    def init_ui(self):

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 20)
        layout.setSpacing(14)

        # ── Título ─────────────────────────────────────
        title_text = "Transferencia bancaria" if self.payment_method == "transfer" else "QR Mercado Pago"
        title = QLabel(title_text)
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ── Total ──────────────────────────────────────
        subtitle = QLabel("Total a cobrar")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        total_label = QLabel(f"$ {int(self.total)}")
        total_label.setObjectName("total")
        total_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(total_label)

        # ── Separador ──────────────────────────────────
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #E2E8F0;")
        layout.addWidget(line)

        # ── Cargar datos de configuración ──────────────
        db = SessionLocal()
        try:
            alias = get_setting(db, "mp_alias", "")
            qr_path = get_setting(db, "payment_qr_path", "")
        finally:
            db.close()

        # ── Alias ──────────────────────────────────────
        if alias:
            alias_subtitle = QLabel("Alias / CBU")
            alias_subtitle.setObjectName("subtitle")
            alias_subtitle.setAlignment(Qt.AlignCenter)
            layout.addWidget(alias_subtitle)

            alias_label = QLabel(alias)
            alias_label.setObjectName("alias")
            alias_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(alias_label)

        # ── QR ─────────────────────────────────────────
        if qr_path and qr_path != "QR no configurado":
            qr_label = QLabel()
            qr_label.setAlignment(Qt.AlignCenter)
            pixmap = QPixmap(qr_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    180, 180,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                qr_label.setPixmap(pixmap)
                layout.addWidget(qr_label)

        # ── Botón imprimir ticket ──────────────────────
        print_btn = QPushButton("🖨️  Imprimir ticket")
        print_btn.setObjectName("print_btn")
        print_btn.setMinimumHeight(52)
        print_btn.clicked.connect(self.print_ticket)
        layout.addWidget(print_btn)

        # ── Cerrar ─────────────────────────────────────
        cancel_btn = QPushButton("Cerrar")
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.clicked.connect(self.accept)
        layout.addWidget(cancel_btn, alignment=Qt.AlignCenter)

    def print_ticket(self):

        from app.printers.ticket_printer import print_ticket

        success, msg = print_ticket(
            self.ticket_id,
            self.cart,
            self.total,
            self.payment_method
        )

        from PySide6.QtWidgets import QMessageBox
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Imprimir")
        msg_box.setText(msg if success else f"Error: {msg}")
        msg_box.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel {
                color: #1E293B;
                font-size: 15px;
                font-weight: bold;
                min-width: 280px;
            }
            QPushButton {
                background-color: #4A6A92;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                min-width: 80px;
                min-height: 32px;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        msg_box.exec()