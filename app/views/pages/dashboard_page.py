from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QScrollArea,
)

from PySide6.QtCore import Qt
from datetime import datetime

from app.assets.themes.theme import PRIMARY_COLOR
from app.database.database import SessionLocal
from app.models.ticket_model import Ticket
from app.models.ticket_item_model import TicketItem
from app.models.product_model import Product
from app.models.cash_session_model import CashSession


class DashboardPage(QWidget):

    def __init__(self):
        super().__init__()

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #F4F5F7; }")

        self.content = QWidget()
        self.content.setStyleSheet("background: #F4F5F7;")

        self.main_layout = QVBoxLayout(self.content)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(20)

        scroll.setWidget(self.content)
        outer_layout.addWidget(scroll)

        self.load_data()

    def load_data(self):

        self.clear_layout(self.main_layout)

        db = SessionLocal()

        try:
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time())

            all_tickets = db.query(Ticket).all()
            tickets_today = [
                t for t in all_tickets
                if t.created_at and t.created_at >= start_of_day
            ]

            products = db.query(Product).filter(Product.is_active == True).all()
            cash_session = db.query(CashSession).filter(CashSession.is_open == True).first()

            total_sales_today = sum(t.total or 0 for t in tickets_today)
            total_tickets_today = len(tickets_today)
            total_products = len(products)
            low_stock = [p for p in products if p.stock <= p.minimum_stock]

            payment_labels = {
                "cash": "Efectivo",
                "transfer": "Transferencia",
                "qr": "QR Mercado Pago",
                "budget": "Presupuesto",
            }

            last_tickets = sorted(
                all_tickets,
                key=lambda t: t.created_at or datetime.min,
                reverse=True
            )[:6]

            # ── Top 10 productos más vendidos ─────────
            from collections import defaultdict
            product_sales = defaultdict(lambda: {"qty": 0, "name": ""})

            all_items = db.query(TicketItem).all()
            product_names = {p.id: p.name for p in db.query(Product).all()}

            for item in all_items:
                pid = item.product_id
                product_sales[pid]["qty"] += item.quantity or 0
                product_sales[pid]["name"] = product_names.get(pid, f"Producto #{pid}")

            top_products = sorted(
                product_sales.items(),
                key=lambda x: x[1]["qty"],
                reverse=True
            )[:10]

        finally:
            db.close()

        # ── Título ────────────────────────────────────
        header_row = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {PRIMARY_COLOR};")
        date_label = QLabel(datetime.now().strftime("%A %d de %B, %Y").capitalize())
        date_label.setStyleSheet("font-size: 13px; color: #94A3B8;")
        date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_row.addWidget(title)
        header_row.addWidget(date_label)
        self.main_layout.addLayout(header_row)

        # ── Cards KPI ─────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)

        if cash_session:
            cash_val = f"$ {int(cash_session.opening_amount)}"
            cash_sub = "● Caja abierta"
            cash_sub_color = "#22C55E"
        else:
            cash_val = "—"
            cash_sub = "● Sin caja"
            cash_sub_color = "#EF4444"

        cards_row.addWidget(self.kpi_card("Ventas hoy", f"$ {int(total_sales_today)}", f"{total_tickets_today} tickets", "#4A6A92"))
        cards_row.addWidget(self.kpi_card("Tickets hoy", str(total_tickets_today), "transacciones", "#0F6E56"))
        cards_row.addWidget(self.kpi_card("Productos", str(total_products), f"{len(low_stock)} con stock bajo", "#854F0B" if low_stock else "#0F6E56"))
        cards_row.addWidget(self.kpi_card("Caja actual", cash_val, cash_sub, cash_sub_color if cash_session else "#EF4444"))
        self.main_layout.addLayout(cards_row)

        # ── Fila inferior ─────────────────────────────
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(14)

        # Últimas ventas
        sales_card = self.section_card("Últimas ventas")
        sales_inner = sales_card.findChild(QVBoxLayout)

        if last_tickets:
            for ticket in last_tickets:
                method = payment_labels.get(ticket.payment_method, ticket.payment_method or "")
                fecha = ticket.created_at.strftime("%d/%m %H:%M") if ticket.created_at else ""
                row = self.list_row(
                    f"#{ticket.id:05d}  ·  {fecha}",
                    f"$ {int(ticket.total or 0)}",
                    method
                )
                sales_inner.addWidget(row)
        else:
            empty = QLabel("Sin ventas registradas")
            empty.setStyleSheet("color: #94A3B8; font-size: 13px; padding: 8px 0;")
            sales_inner.addWidget(empty)

        sales_inner.addStretch()
        bottom_row.addWidget(sales_card, 3)

        # Top 10 productos más vendidos
        top_card = self.section_card("Top 10 productos más vendidos")
        top_inner = top_card.findChild(QVBoxLayout)

        if top_products:
            for i, (pid, data) in enumerate(top_products):
                name = data["name"][:28]
                qty = int(data["qty"])
                row = self.list_row(
                    f"{i+1}. {name}",
                    f"{qty} uni",
                    value_color="#4A6A92"
                )
                top_inner.addWidget(row)
        else:
            empty = QLabel("Sin ventas registradas")
            empty.setStyleSheet("color: #94A3B8; font-size: 13px; padding: 8px 0;")
            top_inner.addWidget(empty)

        top_inner.addStretch()
        bottom_row.addWidget(top_card, 2)

        # Stock bajo
        stock_card = self.section_card("Stock bajo")
        stock_inner = stock_card.findChild(QVBoxLayout)

        if low_stock:
            for product in low_stock[:6]:
                row = self.list_row(
                    product.name,
                    f"{int(product.stock)} uds",
                    f"mín {int(product.minimum_stock)}",
                    value_color="#EF4444"
                )
                stock_inner.addWidget(row)
        else:
            empty = QLabel("Todo el stock en orden")
            empty.setStyleSheet("color: #22C55E; font-size: 13px; padding: 8px 0;")
            stock_inner.addWidget(empty)

        stock_inner.addStretch()
        bottom_row.addWidget(stock_card, 2)

        self.main_layout.addLayout(bottom_row)
        self.main_layout.addStretch()

    def kpi_card(self, title, value, subtitle, accent_color="#4A6A92"):

        frame = QFrame()
        frame.setMinimumHeight(110)
        frame.setStyleSheet("QFrame { background-color: white; border-radius: 14px; }")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 12px; color: #94A3B8; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(lbl_title)

        lbl_value = QLabel(value)
        lbl_value.setStyleSheet("font-size: 28px; font-weight: bold; color: #1E293B;")
        layout.addWidget(lbl_value)

        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet(f"font-size: 12px; color: {accent_color}; font-weight: bold;")
        layout.addWidget(lbl_sub)

        return frame

    def section_card(self, title):

        frame = QFrame()
        frame.setStyleSheet("QFrame { background-color: white; border-radius: 14px; }")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 12px; color: #94A3B8; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(lbl_title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #F1F5F9; margin: 2px 0;")
        layout.addWidget(sep)

        return frame

    def list_row(self, label, value, subtitle="", value_color="#1E293B"):

        row_widget = QWidget()
        row_widget.setStyleSheet("QWidget { border-bottom: 1px solid #F8FAFC; background: transparent; }")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 6, 0, 6)
        row_layout.setSpacing(8)

        left = QVBoxLayout()
        left.setSpacing(1)

        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 13px; color: #1E293B; font-weight: bold; background: transparent; border: none;")
        left.addWidget(lbl)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet("font-size: 11px; color: #94A3B8; background: transparent; border: none;")
            left.addWidget(sub)

        val = QLabel(value)
        val.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {value_color}; background: transparent; border: none;")
        val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        row_layout.addLayout(left)
        row_layout.addWidget(val)

        return row_widget

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())