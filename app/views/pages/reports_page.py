from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QPushButton,
    QDateEdit,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QTabWidget,
    QSizePolicy,
)

from PySide6.QtCore import Qt, QDate
from datetime import datetime, timedelta
from app.assets.themes.theme import PRIMARY_COLOR, BACKGROUND_COLOR
from app.database.database import SessionLocal
from app.models.ticket_model import Ticket
from app.models.ticket_item_model import TicketItem
from app.models.product_model import Product
from app.models.cash_session_model import CashSession

BLUE = "QPushButton { background-color: #4A6A92; color: white; border: none; border-radius: 12px; font-size: 14px; font-weight: bold; padding: 10px 16px; } QPushButton:hover { background-color: #3D5A80; }"
DATE_STYLE = """
    QDateEdit {
        background-color: white;
        border: 2px solid #B8C4D0;
        border-radius: 12px;
        padding: 10px 14px;
        font-size: 14px;
        color: #1E293B;
        min-height: 44px;
        min-width: 140px;
    }
    QDateEdit::drop-down { border: none; width: 24px; }
    QDateEdit:focus { border: 2px solid #4A6A92; }
"""


class ReportsPage(QWidget):

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):

        self.setStyleSheet(f"background-color: {BACKGROUND_COLOR};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        title = QLabel("Reportes")
        title.setStyleSheet(f"font-size: 34px; font-weight: bold; color: {PRIMARY_COLOR};")
        main_layout.addWidget(title)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: transparent; }
            QTabBar::tab {
                background: #E2E8F0; color: #64748B;
                padding: 10px 24px; border-radius: 8px;
                font-size: 14px; font-weight: bold; margin-right: 6px;
            }
            QTabBar::tab:selected { background: #4A6A92; color: white; }
        """)

        tabs.addTab(self.build_sales_report(), "Ventas por período")
        tabs.addTab(self.build_products_report(), "Productos más vendidos")
        tabs.addTab(self.build_cash_report(), "Movimientos de caja")

        main_layout.addWidget(tabs)

    # ── Tab Ventas por período ────────────────────────

    def build_sales_report(self):

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(14)

        # Filtros
        filter_frame = QFrame()
        filter_frame.setStyleSheet("background-color: white; border-radius: 16px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(20, 16, 20, 16)
        filter_layout.setSpacing(12)

        from_label = QLabel("Desde:")
        from_label.setStyleSheet("font-size: 13px; color: #64748B; font-weight: bold; background: transparent;")
        from_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.sales_from_date = QDateEdit()
        self.sales_from_date.setDate(QDate.currentDate().addDays(-30))
        self.sales_from_date.setCalendarPopup(True)
        self.sales_from_date.setDisplayFormat("dd/MM/yyyy")
        self.sales_from_date.setStyleSheet(DATE_STYLE)
        self.sales_from_date.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        to_label = QLabel("Hasta:")
        to_label.setStyleSheet("font-size: 13px; color: #64748B; font-weight: bold; background: transparent;")
        to_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.sales_to_date = QDateEdit()
        self.sales_to_date.setDate(QDate.currentDate())
        self.sales_to_date.setCalendarPopup(True)
        self.sales_to_date.setDisplayFormat("dd/MM/yyyy")
        self.sales_to_date.setStyleSheet(DATE_STYLE)
        self.sales_to_date.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        btn_filter = QPushButton("Generar reporte")
        btn_filter.setStyleSheet(BLUE)
        btn_filter.setFixedHeight(44)
        btn_filter.clicked.connect(self.load_sales_report)

        btn_export = QPushButton("Exportar Excel")
        btn_export.setStyleSheet(BLUE)
        btn_export.setFixedHeight(44)
        btn_export.clicked.connect(self.export_sales_report)

        self.sales_total_label = QLabel("Total: $ 0")
        self.sales_total_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #4A6A92; background: transparent;")

        filter_layout.addWidget(from_label)
        filter_layout.addWidget(self.sales_from_date)
        filter_layout.addSpacing(8)
        filter_layout.addWidget(to_label)
        filter_layout.addWidget(self.sales_to_date)
        filter_layout.addSpacing(8)
        filter_layout.addWidget(btn_filter)
        filter_layout.addWidget(btn_export)
        filter_layout.addStretch()
        filter_layout.addWidget(self.sales_total_label)

        layout.addWidget(filter_frame)

        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(5)
        self.sales_table.setHorizontalHeaderLabels([
            "N° Ticket", "Fecha", "Usuario", "Método pago", "Total"
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sales_table.verticalHeader().setVisible(False)
        self.sales_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.sales_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sales_table.setStyleSheet(self.table_style())
        layout.addWidget(self.sales_table)

        self.load_sales_report()
        return widget

    # ── Tab Productos más vendidos ────────────────────

    def build_products_report(self):

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(14)

        filter_frame = QFrame()
        filter_frame.setStyleSheet("background-color: white; border-radius: 16px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(20, 16, 20, 16)
        filter_layout.setSpacing(12)

        from_label = QLabel("Desde:")
        from_label.setStyleSheet("font-size: 13px; color: #64748B; font-weight: bold; background: transparent;")
        from_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.prod_from_date = QDateEdit()
        self.prod_from_date.setDate(QDate.currentDate().addDays(-30))
        self.prod_from_date.setCalendarPopup(True)
        self.prod_from_date.setDisplayFormat("dd/MM/yyyy")
        self.prod_from_date.setStyleSheet(DATE_STYLE)
        self.prod_from_date.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        to_label = QLabel("Hasta:")
        to_label.setStyleSheet("font-size: 13px; color: #64748B; font-weight: bold; background: transparent;")
        to_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.prod_to_date = QDateEdit()
        self.prod_to_date.setDate(QDate.currentDate())
        self.prod_to_date.setCalendarPopup(True)
        self.prod_to_date.setDisplayFormat("dd/MM/yyyy")
        self.prod_to_date.setStyleSheet(DATE_STYLE)
        self.prod_to_date.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        btn_filter = QPushButton("Generar reporte")
        btn_filter.setStyleSheet(BLUE)
        btn_filter.setFixedHeight(44)
        btn_filter.clicked.connect(self.load_products_report)

        btn_export = QPushButton("Exportar Excel")
        btn_export.setStyleSheet(BLUE)
        btn_export.setFixedHeight(44)
        btn_export.clicked.connect(self.export_products_report)

        filter_layout.addWidget(from_label)
        filter_layout.addWidget(self.prod_from_date)
        filter_layout.addSpacing(8)
        filter_layout.addWidget(to_label)
        filter_layout.addWidget(self.prod_to_date)
        filter_layout.addSpacing(8)
        filter_layout.addWidget(btn_filter)
        filter_layout.addWidget(btn_export)
        filter_layout.addStretch()

        layout.addWidget(filter_frame)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(4)
        self.products_table.setHorizontalHeaderLabels([
            "Posición", "Producto", "Unidades vendidas", "Total facturado"
        ])
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_table.setStyleSheet(self.table_style())
        layout.addWidget(self.products_table)

        self.load_products_report()
        return widget

    # ── Tab Movimientos de caja ───────────────────────

    def build_cash_report(self):

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(14)

        filter_frame = QFrame()
        filter_frame.setStyleSheet("background-color: white; border-radius: 16px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(20, 16, 20, 16)
        filter_layout.setSpacing(12)

        from_label = QLabel("Desde:")
        from_label.setStyleSheet("font-size: 13px; color: #64748B; font-weight: bold; background: transparent;")
        from_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.cash_from_date = QDateEdit()
        self.cash_from_date.setDate(QDate.currentDate().addDays(-30))
        self.cash_from_date.setCalendarPopup(True)
        self.cash_from_date.setDisplayFormat("dd/MM/yyyy")
        self.cash_from_date.setStyleSheet(DATE_STYLE)
        self.cash_from_date.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        to_label = QLabel("Hasta:")
        to_label.setStyleSheet("font-size: 13px; color: #64748B; font-weight: bold; background: transparent;")
        to_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.cash_to_date = QDateEdit()
        self.cash_to_date.setDate(QDate.currentDate())
        self.cash_to_date.setCalendarPopup(True)
        self.cash_to_date.setDisplayFormat("dd/MM/yyyy")
        self.cash_to_date.setStyleSheet(DATE_STYLE)
        self.cash_to_date.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        btn_filter = QPushButton("Generar reporte")
        btn_filter.setStyleSheet(BLUE)
        btn_filter.setFixedHeight(44)
        btn_filter.clicked.connect(self.load_cash_report)

        btn_export = QPushButton("Exportar Excel")
        btn_export.setStyleSheet(BLUE)
        btn_export.setFixedHeight(44)
        btn_export.clicked.connect(self.export_cash_report)

        filter_layout.addWidget(from_label)
        filter_layout.addWidget(self.cash_from_date)
        filter_layout.addSpacing(8)
        filter_layout.addWidget(to_label)
        filter_layout.addWidget(self.cash_to_date)
        filter_layout.addSpacing(8)
        filter_layout.addWidget(btn_filter)
        filter_layout.addWidget(btn_export)
        filter_layout.addStretch()

        layout.addWidget(filter_frame)

        self.cash_table = QTableWidget()
        self.cash_table.setColumnCount(6)
        self.cash_table.setHorizontalHeaderLabels([
            "Fecha apertura", "Fecha cierre", "Usuario", "Apertura", "Cierre", "Diferencia"
        ])
        self.cash_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cash_table.verticalHeader().setVisible(False)
        self.cash_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cash_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cash_table.setStyleSheet(self.table_style())
        layout.addWidget(self.cash_table)

        self.load_cash_report()
        return widget

    # ── Lógica reportes ───────────────────────────────

    def get_date_range(self, from_date_edit, to_date_edit):
        from_date = datetime.combine(from_date_edit.date().toPython(), datetime.min.time())
        to_date = datetime.combine(to_date_edit.date().toPython(), datetime.max.time().replace(microsecond=0))
        return from_date, to_date

    def load_sales_report(self):

        from_date, to_date = self.get_date_range(self.sales_from_date, self.sales_to_date)

        db = SessionLocal()
        try:
            tickets = db.query(Ticket).filter(
                Ticket.created_at >= from_date,
                Ticket.created_at <= to_date
            ).order_by(Ticket.created_at.desc()).all()
        finally:
            db.close()

        payment_labels = {
            "cash": "Efectivo",
            "transfer": "Transferencia",
            "qr": "QR Mercado Pago",
            "budget": "Presupuesto",
        }

        self.sales_table.setRowCount(0)
        total = 0

        for row, ticket in enumerate(tickets):
            self.sales_table.insertRow(row)
            total += ticket.total or 0

            self.sales_table.setItem(row, 0, QTableWidgetItem(f"#{ticket.id:05d}"))
            self.sales_table.setItem(row, 1, QTableWidgetItem(
                ticket.created_at.strftime("%d/%m/%Y %H:%M") if ticket.created_at else ""
            ))
            self.sales_table.setItem(row, 2, QTableWidgetItem(ticket.username or ""))
            self.sales_table.setItem(row, 3, QTableWidgetItem(
                payment_labels.get(ticket.payment_method, ticket.payment_method or "")
            ))
            total_item = QTableWidgetItem(f"$ {int(ticket.total or 0)}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.sales_table.setItem(row, 4, total_item)

        self.sales_total_label.setText(f"Total: $ {int(total)}")

    def load_products_report(self):

        from_date, to_date = self.get_date_range(self.prod_from_date, self.prod_to_date)

        db = SessionLocal()
        try:
            tickets = db.query(Ticket).filter(
                Ticket.created_at >= from_date,
                Ticket.created_at <= to_date
            ).all()

            ticket_ids = [t.id for t in tickets]

            from collections import defaultdict
            product_data = defaultdict(lambda: {"qty": 0, "total": 0.0, "name": ""})

            if ticket_ids:
                items = db.query(TicketItem).filter(
                    TicketItem.ticket_id.in_(ticket_ids)
                ).all()

                product_names = {p.id: p.name for p in db.query(Product).all()}

                for item in items:
                    pid = item.product_id
                    product_data[pid]["qty"] += item.quantity or 0
                    product_data[pid]["total"] += item.subtotal or 0
                    product_data[pid]["name"] = product_names.get(pid, f"Producto #{pid}")

        finally:
            db.close()

        sorted_products = sorted(
            product_data.items(),
            key=lambda x: x[1]["qty"],
            reverse=True
        )

        self.products_table.setRowCount(0)

        for pos, (pid, data) in enumerate(sorted_products):
            row = pos
            self.products_table.insertRow(row)

            pos_item = QTableWidgetItem(f"#{pos + 1}")
            pos_item.setTextAlignment(Qt.AlignCenter)
            self.products_table.setItem(row, 0, pos_item)

            self.products_table.setItem(row, 1, QTableWidgetItem(data["name"]))

            qty_item = QTableWidgetItem(str(int(data["qty"])))
            qty_item.setTextAlignment(Qt.AlignCenter)
            self.products_table.setItem(row, 2, qty_item)

            total_item = QTableWidgetItem(f"$ {int(data['total'])}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.products_table.setItem(row, 3, total_item)

    def load_cash_report(self):

        from_date, to_date = self.get_date_range(self.cash_from_date, self.cash_to_date)

        db = SessionLocal()
        try:
            sessions = db.query(CashSession).filter(
                CashSession.opened_at >= from_date,
                CashSession.opened_at <= to_date
            ).order_by(CashSession.opened_at.desc()).all()
        finally:
            db.close()

        self.cash_table.setRowCount(0)

        for row, session in enumerate(sessions):
            self.cash_table.insertRow(row)

            self.cash_table.setItem(row, 0, QTableWidgetItem(
                session.opened_at.strftime("%d/%m/%Y %H:%M") if session.opened_at else ""
            ))
            self.cash_table.setItem(row, 1, QTableWidgetItem(
                session.closed_at.strftime("%d/%m/%Y %H:%M") if session.closed_at else "Abierta"
            ))
            self.cash_table.setItem(row, 2, QTableWidgetItem(session.username or ""))

            apertura_item = QTableWidgetItem(f"$ {int(session.opening_amount or 0)}")
            apertura_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.cash_table.setItem(row, 3, apertura_item)

            cierre_item = QTableWidgetItem(
                f"$ {int(session.closing_amount or 0)}" if session.closing_amount else "—"
            )
            cierre_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.cash_table.setItem(row, 4, cierre_item)

            diff = session.difference or 0
            diff_item = QTableWidgetItem(f"$ {int(diff)}")
            diff_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            from PySide6.QtCore import Qt as QtCore
            diff_item.setForeground(Qt.darkGreen if diff >= 0 else Qt.red)
            self.cash_table.setItem(row, 5, diff_item)

    # ── Exportar Excel ────────────────────────────────

    def export_sales_report(self):
        import pandas as pd

        from_date, to_date = self.get_date_range(self.sales_from_date, self.sales_to_date)

        db = SessionLocal()
        try:
            tickets = db.query(Ticket).filter(
                Ticket.created_at >= from_date,
                Ticket.created_at <= to_date
            ).order_by(Ticket.created_at.desc()).all()
        finally:
            db.close()

        payment_labels = {
            "cash": "Efectivo", "transfer": "Transferencia",
            "qr": "QR Mercado Pago", "budget": "Presupuesto",
        }

        data = [{
            "N° Ticket": f"#{t.id:05d}",
            "Fecha": t.created_at.strftime("%d/%m/%Y %H:%M") if t.created_at else "",
            "Usuario": t.username or "",
            "Método pago": payment_labels.get(t.payment_method, t.payment_method or ""),
            "Total": int(t.total or 0),
        } for t in tickets]

        self._export_to_excel(data, "reporte_ventas.xlsx")

    def export_products_report(self):
        import pandas as pd

        from_date, to_date = self.get_date_range(self.prod_from_date, self.prod_to_date)

        db = SessionLocal()
        try:
            tickets = db.query(Ticket).filter(
                Ticket.created_at >= from_date,
                Ticket.created_at <= to_date
            ).all()
            ticket_ids = [t.id for t in tickets]

            from collections import defaultdict
            product_data = defaultdict(lambda: {"qty": 0, "total": 0.0, "name": ""})

            if ticket_ids:
                items = db.query(TicketItem).filter(TicketItem.ticket_id.in_(ticket_ids)).all()
                product_names = {p.id: p.name for p in db.query(Product).all()}
                for item in items:
                    pid = item.product_id
                    product_data[pid]["qty"] += item.quantity or 0
                    product_data[pid]["total"] += item.subtotal or 0
                    product_data[pid]["name"] = product_names.get(pid, f"Producto #{pid}")
        finally:
            db.close()

        sorted_products = sorted(product_data.items(), key=lambda x: x[1]["qty"], reverse=True)

        data = [{
            "Posición": f"#{pos + 1}",
            "Producto": d["name"],
            "Unidades vendidas": int(d["qty"]),
            "Total facturado": int(d["total"]),
        } for pos, (_, d) in enumerate(sorted_products)]

        self._export_to_excel(data, "reporte_productos.xlsx")

    def export_cash_report(self):
        import pandas as pd

        from_date, to_date = self.get_date_range(self.cash_from_date, self.cash_to_date)

        db = SessionLocal()
        try:
            sessions = db.query(CashSession).filter(
                CashSession.opened_at >= from_date,
                CashSession.opened_at <= to_date
            ).order_by(CashSession.opened_at.desc()).all()
        finally:
            db.close()

        data = [{
            "Apertura": s.opened_at.strftime("%d/%m/%Y %H:%M") if s.opened_at else "",
            "Cierre": s.closed_at.strftime("%d/%m/%Y %H:%M") if s.closed_at else "Abierta",
            "Usuario": s.username or "",
            "Monto apertura": int(s.opening_amount or 0),
            "Monto cierre": int(s.closing_amount or 0) if s.closing_amount else 0,
            "Diferencia": int(s.difference or 0),
        } for s in sessions]

        self._export_to_excel(data, "reporte_caja.xlsx")

    def _export_to_excel(self, data, default_name):
        import pandas as pd

        if not data:
            self.show_message("Aviso", "No hay datos para exportar")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar reporte", default_name, "Excel Files (*.xlsx)"
        )
        if not file_path:
            return

        try:
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)
            self.show_message("OK", "Reporte exportado correctamente")
        except Exception as e:
            self.show_message("Error", str(e))

    def table_style(self):
        return """
            QTableWidget { background-color: white; border-radius: 16px; font-size: 14px; color: #1E293B; border: none; }
            QHeaderView::section { background-color: #4A6A92; color: white; padding: 12px; border: none; font-weight: bold; }
            QTableWidget::item { padding: 10px; }
            QTableWidget::item:selected { background-color: #DBEAFE; color: #1E293B; }
        """

    def show_message(self, title, message):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1E293B; font-size: 15px; font-weight: bold; min-width: 300px; }
            QPushButton {
                background-color: #4A6A92; color: white; border: none;
                border-radius: 10px; padding: 10px 20px; min-width: 80px;
                min-height: 32px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #3D5A80; }
        """)
        msg.exec()