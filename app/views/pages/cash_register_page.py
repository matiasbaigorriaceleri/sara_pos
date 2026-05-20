
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QFrame,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QHBoxLayout,
)

from PySide6.QtCore import Qt

from app.assets.themes.theme import (
    PRIMARY_COLOR,
    INPUT_STYLE,
    BUTTON_STYLE,
)

from app.database.database import SessionLocal

from app.models.cash_session_model import CashSession

from app.models.ticket_model import Ticket


class CashRegisterPage(QWidget):

    def __init__(self, username=None):
        super().__init__()

        self.username = username or "admin"

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignTop)

        title = QLabel("Arqueo Caja")
        title.setStyleSheet(f"""
            font-size: 32px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        """)
        main_layout.addWidget(title)

        subtitle = QLabel("Realice la apertura y cierre de caja.")
        subtitle.setStyleSheet("""
            font-size: 15px;
            color: #94A3B8;
            margin-bottom: 10px;
        """)
        main_layout.addWidget(subtitle)

        card = QFrame()
        card.setMaximumWidth(950)
        card.setStyleSheet("""
            background-color: white;
            border-radius: 20px;
        """)

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(25, 25, 25, 25)
        card_layout.setSpacing(20)

        open_title = QLabel("1. Apertura de caja")
        open_title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1E293B;
        """)
        card_layout.addWidget(open_title)

        self.open_amount_input = QLineEdit()
        self.open_amount_input.setPlaceholderText("Monto apertura caja")
        self.open_amount_input.setMinimumHeight(55)
        self.open_amount_input.setStyleSheet(INPUT_STYLE)
        self.open_amount_input.returnPressed.connect(self.open_cash)
        card_layout.addWidget(self.open_amount_input)

        open_button = QPushButton("Abrir Caja")
        open_button.setMinimumHeight(55)
        open_button.setStyleSheet(BUTTON_STYLE)
        open_button.clicked.connect(self.open_cash)
        card_layout.addWidget(open_button)

        close_title = QLabel("2. Cierre de caja")
        close_title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1E293B;
            margin-top: 10px;
        """)
        card_layout.addWidget(close_title)

        self.close_amount_input = QLineEdit()
        self.close_amount_input.setPlaceholderText("Monto real cierre caja")
        self.close_amount_input.setMinimumHeight(55)
        self.close_amount_input.setStyleSheet(INPUT_STYLE)
        self.close_amount_input.returnPressed.connect(self.close_cash)
        card_layout.addWidget(self.close_amount_input)

        close_button = QPushButton("Cerrar Caja")
        close_button.setMinimumHeight(55)
        close_button.setStyleSheet(BUTTON_STYLE)
        close_button.clicked.connect(self.close_cash)
        card_layout.addWidget(close_button)

        summary_title = QLabel("3. Resumen")
        summary_title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1E293B;
            margin-top: 10px;
        """)
        card_layout.addWidget(summary_title)

        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(15)

        self.open_card = self.create_summary_card("Apertura", "$ 0")
        self.sales_card = self.create_summary_card("Ventas", "$ 0")
        self.expected_card = self.create_summary_card("Esperado", "$ 0")
        self.difference_card = self.create_summary_card("Diferencia", "$ 0")

        summary_layout.addWidget(self.open_card)
        summary_layout.addWidget(self.sales_card)
        summary_layout.addWidget(self.expected_card)
        summary_layout.addWidget(self.difference_card)

        card_layout.addLayout(summary_layout)

        card.setLayout(card_layout)

        main_layout.addWidget(card)
        main_layout.addStretch()

        self.setLayout(main_layout)

        self.refresh_summary()

    def create_summary_card(self, title, value):

        frame = QFrame()
        frame.setMinimumHeight(120)
        frame.setStyleSheet("""
            background-color: #F8FAFC;
            border-radius: 16px;
            border: 1px solid #E2E8F0;
        """)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 15px;
            color: #64748B;
            font-weight: bold;
        """)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        """)

        frame.value_label = value_label

        layout.addWidget(title_label, alignment=Qt.AlignCenter)
        layout.addWidget(value_label, alignment=Qt.AlignCenter)

        frame.setLayout(layout)

        return frame

    def open_cash(self):

        amount_text = self.open_amount_input.text().strip()

        if not amount_text:
            QMessageBox.warning(
                self,
                "Error",
                "Ingrese monto apertura"
            )
            return

        try:
            opening_amount = int(float(amount_text))
        except ValueError:
            QMessageBox.warning(
                self,
                "Error",
                "El monto de apertura debe ser numérico"
            )
            return

        db = SessionLocal()

        open_session = db.query(CashSession).filter(
            CashSession.is_open == True
        ).first()

        if open_session:
            db.close()

            QMessageBox.warning(
                self,
                "Error",
                "Ya existe una caja abierta"
            )
            return

        session = CashSession(
            username=self.username,
            opening_amount=opening_amount,
            closing_amount=0,
            expected_amount=opening_amount,
            difference=0,
            opened_at=datetime.now(),
            closed_at=None,
            is_open=True
        )

        db.add(session)
        db.commit()
        db.close()

        QMessageBox.information(
            self,
            "Correcto",
            "Caja abierta"
        )

        self.open_amount_input.clear()
        self.refresh_summary()

    def close_cash(self):

        amount_text = self.close_amount_input.text().strip()

        if not amount_text:
            QMessageBox.warning(
                self,
                "Error",
                "Ingrese monto cierre"
            )
            return

        try:
            closing_amount = int(float(amount_text))
        except ValueError:
            QMessageBox.warning(
                self,
                "Error",
                "El monto de cierre debe ser numérico"
            )
            return

        db = SessionLocal()

        session = db.query(CashSession).filter(
            CashSession.is_open == True
        ).first()

        if not session:
            db.close()

            QMessageBox.warning(
                self,
                "Error",
                "No hay caja abierta"
            )
            return

        tickets = db.query(Ticket).filter(
            Ticket.cash_session_id == session.id
        ).all()

        total_sales = sum(ticket.total for ticket in tickets)

        expected_amount = session.opening_amount + total_sales

        difference = closing_amount - expected_amount

        session.closing_amount = closing_amount
        session.expected_amount = expected_amount
        session.difference = difference
        session.closed_at = datetime.now()
        session.is_open = False

        db.commit()
        db.close()

        QMessageBox.information(
            self,
            "Caja cerrada",
            (
                f"Ventas: $ {total_sales}\n"
                f"Esperado: $ {expected_amount}\n"
                f"Real: $ {closing_amount}\n"
                f"Diferencia: $ {difference}"
            )
        )

        self.close_amount_input.clear()
        self.refresh_summary()

    def refresh_summary(self):

        db = SessionLocal()

        session = db.query(CashSession).order_by(
            CashSession.id.desc()
        ).first()

        if not session:
            db.close()
            return

        tickets = db.query(Ticket).filter(
            Ticket.cash_session_id == session.id
        ).all()

        total_sales = sum(ticket.total for ticket in tickets)

        expected_amount = session.opening_amount + total_sales

        db.close()

        self.open_card.value_label.setText(
            f"$ {session.opening_amount}"
        )

        self.sales_card.value_label.setText(
            f"$ {total_sales}"
        )

        self.expected_card.value_label.setText(
            f"$ {expected_amount}"
        )

        self.difference_card.value_label.setText(
            f"$ {session.difference}"
        )