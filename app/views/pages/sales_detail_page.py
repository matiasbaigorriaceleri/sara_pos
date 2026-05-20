from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

from app.assets.themes.theme import (
    PRIMARY_COLOR,
)

from app.database.database import SessionLocal

from app.models.ticket_model import Ticket


class SalesDetailPage(QWidget):

    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout()

        # =====================================
        # TITLE
        # =====================================

        title = QLabel("Detalle de Ventas")

        title.setStyleSheet(f"""
            font-size: 34px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        """)

        main_layout.addWidget(title)

        # =====================================
        # TABLE
        # =====================================

        self.table = QTableWidget()

        self.table.setColumnCount(5)

        self.table.setHorizontalHeaderLabels([
            "ID",
            "Fecha",
            "Usuario",
            "Productos",
            "Total",
        ])

        self.table.horizontalHeader().setStretchLastSection(True)

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

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
            }
        """)

        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

        self.load_tickets()

    # =====================================
    # LOAD TICKETS
    # =====================================

    def load_tickets(self):

        db = SessionLocal()

        tickets = db.query(Ticket).order_by(
            Ticket.id.desc()
        ).all()

        self.table.setRowCount(len(tickets))

        for row, ticket in enumerate(tickets):

            self.table.setItem(
                row,
                0,
                QTableWidgetItem(str(ticket.id))
            )

            self.table.setItem(
                row,
                1,
                QTableWidgetItem(
                    str(ticket.created_at.strftime("%d/%m/%Y %H:%M"))
                )
            )

            self.table.setItem(
                row,
                2,
                QTableWidgetItem(ticket.username)
            )

            self.table.setItem(
                row,
                3,
                QTableWidgetItem(ticket.products)
            )

            self.table.setItem(
                row,
                4,
                QTableWidgetItem(f"$ {ticket.total}")
            )

        db.close()

    # =====================================
    # REFRESH
    # =====================================

    def refresh_data(self):

        self.load_tickets()