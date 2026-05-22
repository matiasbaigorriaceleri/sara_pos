from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)

from PySide6.QtCore import Qt


class PaymentDialog(QDialog):

    def __init__(self, total, parent=None):
        super().__init__(parent)

        self.total = total
        self.selected_method = None

        self.setWindowTitle("Cobrar venta")
        self.setFixedSize(480, 380)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog {
                background-color: #F4F5F7;
            }
            QLabel#title {
                font-size: 22px;
                font-weight: bold;
                color: #1E293B;
            }
            QLabel#total {
                font-size: 36px;
                font-weight: bold;
                color: #4A6A92;
            }
            QLabel#subtitle {
                font-size: 15px;
                color: #64748B;
            }
            QPushButton.method {
                background-color: white;
                color: #1E293B;
                border: 2px solid #B8C4D0;
                border-radius: 12px;
                padding: 18px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton.method:hover {
                background-color: #D8E6F5;
                border: 2px solid #4A6A92;
                color: #4A6A92;
            }
            QPushButton#cancel {
                background-color: transparent;
                color: #64748B;
                border: none;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton#cancel:hover {
                color: #FF003D;
            }
        """)

        self.init_ui()

    def init_ui(self):

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 20)
        layout.setSpacing(16)

        # ── Título ────────────────────────────────────
        title = QLabel("Seleccionar método de pago")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ── Total ─────────────────────────────────────
        subtitle = QLabel("Total a cobrar")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        total_label = QLabel(f"$ {int(self.total)}")
        total_label.setObjectName("total")
        total_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(total_label)

        # ── Separador ─────────────────────────────────
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #E2E8F0;")
        layout.addWidget(line)

        # ── Botones de método ─────────────────────────
        row1 = QHBoxLayout()
        row2 = QHBoxLayout()

        btn_cash = self.create_method_button("💵  Efectivo", "cash")
        btn_transfer = self.create_method_button("🏦  Transferencia", "transfer")
        btn_qr = self.create_method_button("📱  QR Mercado Pago", "qr")
        btn_budget = self.create_method_button("📄  Presupuesto", "budget")

        row1.addWidget(btn_cash)
        row1.addWidget(btn_transfer)
        row2.addWidget(btn_qr)
        row2.addWidget(btn_budget)

        layout.addLayout(row1)
        layout.addLayout(row2)

        # ── Cancelar ──────────────────────────────────
        cancel_button = QPushButton("Cancelar")
        cancel_button.setObjectName("cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button, alignment=Qt.AlignCenter)

    def create_method_button(self, text, method):

        button = QPushButton(text)
        button.setProperty("class", "method")
        button.setMinimumHeight(64)
        button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #1E293B;
                border: 2px solid #B8C4D0;
                border-radius: 12px;
                padding: 18px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D8E6F5;
                border: 2px solid #4A6A92;
                color: #4A6A92;
            }
        """)
        button.clicked.connect(
            lambda: self.select_method(method)
        )
        return button

    def select_method(self, method):
        self.selected_method = method
        self.accept()