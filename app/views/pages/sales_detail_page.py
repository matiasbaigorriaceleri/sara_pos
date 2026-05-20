from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QFrame,
    QDialog,
    QMessageBox,
)

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from app.assets.themes.theme import PRIMARY_COLOR
from app.database.database import SessionLocal
from app.models.ticket_model import Ticket
from app.models.ticket_item_model import TicketItem
from app.models.product_model import Product


class SalesDetailPage(QWidget):

    def __init__(self):
        super().__init__()

        self.all_tickets = []

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # ── Título ────────────────────────────────────
        title = QLabel("Detalle de Ventas")
        title.setStyleSheet(f"""
            font-size: 34px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        """)
        main_layout.addWidget(title)

        # ── Filtros ───────────────────────────────────
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                padding: 4px;
            }
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        filter_layout.setSpacing(10)

        btn_hoy = self.create_filter_button("Hoy")
        btn_hoy.clicked.connect(lambda: self.filter_by("hoy"))
        filter_layout.addWidget(btn_hoy)

        btn_semana = self.create_filter_button("Esta semana")
        btn_semana.clicked.connect(lambda: self.filter_by("semana"))
        filter_layout.addWidget(btn_semana)

        btn_mes = self.create_filter_button("Este mes")
        btn_mes.clicked.connect(lambda: self.filter_by("mes"))
        filter_layout.addWidget(btn_mes)

        btn_todos = self.create_filter_button("Todos", active=True)
        btn_todos.clicked.connect(lambda: self.filter_by("todos"))
        filter_layout.addWidget(btn_todos)

        filter_layout.addStretch()

        self.total_label = QLabel("Total: $ 0")
        self.total_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #4A6A92;
        """)
        filter_layout.addWidget(self.total_label)

        main_layout.addWidget(filter_frame)

        # ── Tabla ─────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "N° Ticket", "Fecha", "Usuario", "Método pago", "Total", "Acciones"
        ])

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 160)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 16px;
                padding: 10px;
                font-size: 15px;
                gridline-color: #E5E7EB;
                color: #1E293B;
            }
            QHeaderView::section {
                background-color: #4A6A92;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
            QTableWidget::item:selected {
                background-color: #D8E6F5;
                color: #1E293B;
            }
        """)

        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        self.load_tickets()

    def create_filter_button(self, text, active=False):
        btn = QPushButton(text)
        btn.setMinimumHeight(36)
        btn.setCursor(Qt.PointingHandCursor)
        if active:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4A6A92;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 6px 16px;
                    font-size: 13px;
                    font-weight: bold;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #F1F5F9;
                    color: #4A6A92;
                    border: 1px solid #B8C4D0;
                    border-radius: 8px;
                    padding: 6px 16px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #D8E6F5;
                }
            """)
        return btn

    def load_tickets(self):

        db = SessionLocal()

        try:
            self.all_tickets = db.query(Ticket).order_by(
                Ticket.id.desc()
            ).all()
        finally:
            db.close()

        self.render_tickets(self.all_tickets)

    def filter_by(self, period):

        from datetime import datetime, timedelta

        now = datetime.now()

        if period == "hoy":
            filtered = [
                t for t in self.all_tickets
                if t.created_at.date() == now.date()
            ]
        elif period == "semana":
            week_ago = now - timedelta(days=7)
            filtered = [
                t for t in self.all_tickets
                if t.created_at >= week_ago
            ]
        elif period == "mes":
            month_ago = now - timedelta(days=30)
            filtered = [
                t for t in self.all_tickets
                if t.created_at >= month_ago
            ]
        else:
            filtered = self.all_tickets

        self.render_tickets(filtered)

    def render_tickets(self, tickets):

        self.table.setRowCount(len(tickets))

        total_sum = 0

        payment_labels = {
            "cash": "Efectivo",
            "transfer": "Transferencia",
            "qr": "QR Mercado Pago",
            "budget": "Presupuesto",
        }

        for row, ticket in enumerate(tickets):

            total_sum += ticket.total or 0

            # N° Ticket
            id_item = QTableWidgetItem(f"#{ticket.id:05d}")
            id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, id_item)

            # Fecha
            fecha = ticket.created_at.strftime("%d/%m/%Y %H:%M") if ticket.created_at else ""
            fecha_item = QTableWidgetItem(fecha)
            fecha_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, fecha_item)

            # Usuario
            user_item = QTableWidgetItem(ticket.username or "")
            user_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, user_item)

            # Método pago
            method = payment_labels.get(ticket.payment_method, ticket.payment_method or "")
            method_item = QTableWidgetItem(method)
            method_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, method_item)

            # Total
            total_item = QTableWidgetItem(f"$ {int(ticket.total or 0)}")
            total_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, total_item)

            # Botón ver detalle
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(6, 4, 6, 4)

            btn_detail = QPushButton("Ver detalle")
            btn_detail.setStyleSheet("""
                QPushButton {
                    background-color: #4A6A92;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #3D5A80;
                }
            """)
            btn_detail.setCursor(Qt.PointingHandCursor)
            btn_detail.clicked.connect(
                lambda checked, t=ticket: self.show_ticket_detail(t)
            )
            btn_layout.addWidget(btn_detail)
            self.table.setCellWidget(row, 5, btn_widget)

        self.total_label.setText(f"Total: $ {int(total_sum)}")

    def show_ticket_detail(self, ticket):

        db = SessionLocal()

        try:
            items = db.query(TicketItem).filter(
                TicketItem.ticket_id == ticket.id
            ).all()

            detail_lines = []
            for item in items:
                product = db.query(Product).filter(
                    Product.id == item.product_id
                ).first()
                name = product.name if product else f"Producto #{item.product_id}"
                detail_lines.append(
                    f"• {name}  x{int(item.quantity)}  →  $ {int(item.subtotal)}"
                )
        finally:
            db.close()

        payment_labels = {
            "cash": "Efectivo",
            "transfer": "Transferencia",
            "qr": "QR Mercado Pago",
            "budget": "Presupuesto",
        }

        method = payment_labels.get(ticket.payment_method, ticket.payment_method or "")
        fecha = ticket.created_at.strftime("%d/%m/%Y %H:%M") if ticket.created_at else ""

        detail_text = "\n".join(detail_lines) if detail_lines else "Sin detalle disponible"

        msg = QMessageBox(self)
        msg.setWindowTitle(f"Ticket #{ticket.id:05d}")
        msg.setText(
            f"Fecha: {fecha}\n"
            f"Usuario: {ticket.username}\n"
            f"Método: {method}\n"
            f"─────────────────────\n"
            f"{detail_text}\n"
            f"─────────────────────\n"
            f"TOTAL: $ {int(ticket.total or 0)}"
        )
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel {
                color: #1E293B;
                font-size: 14px;
                min-width: 340px;
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
            QPushButton:hover { background-color: #3D5A80; }
        """)
        msg.exec()

    def load_sales(self):
        self.load_tickets()