from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
    QTabWidget,
    QDateEdit,
    QCheckBox,
)

from PySide6.QtCore import Qt, QDate
from app.database.database import SessionLocal
from app.models.client_model import Client
from app.models.client_account_model import ClientAccount
from app.assets.themes.theme import PRIMARY_COLOR, BACKGROUND_COLOR, INPUT_STYLE
from datetime import datetime

BLUE = "QPushButton { background-color: #4A6A92; color: white; border: none; border-radius: 12px; font-size: 15px; font-weight: bold; } QPushButton:hover { background-color: #3D5A80; }"
RED = "QPushButton { background-color: #FF003D; color: white; border: none; border-radius: 12px; font-size: 15px; font-weight: bold; } QPushButton:hover { background-color: #D90429; }"


class ClientsPage(QWidget):

    def __init__(self):
        super().__init__()
        self.selected_client_id = None
        self.setup_ui()

    def setup_ui(self):

        self.setStyleSheet(f"background-color: {BACKGROUND_COLOR};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        title = QLabel("Clientes")
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

        tabs.addTab(self.build_clients_tab(), "ABM Clientes")
        tabs.addTab(self.build_accounts_tab(), "Cuenta Corriente")

        main_layout.addWidget(tabs)

    # ── Tab ABM Clientes ──────────────────────────────

    def build_clients_tab(self):

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(14)

        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: white; border-radius: 16px;")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(12)

        row1 = QHBoxLayout()
        self.cli_name_input = self.create_input("Nombre cliente *")
        self.cli_phone_input = self.create_input("Teléfono")
        self.cli_email_input = self.create_input("Email")
        row1.addWidget(self.cli_name_input)
        row1.addWidget(self.cli_phone_input)
        row1.addWidget(self.cli_email_input)
        form_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.cli_address_input = self.create_input("Dirección")
        self.cli_notes_input = self.create_input("Notas")

        self.cli_discount_input = self.create_input("Descuento % (ej: 10)")
        self.cli_discount_input.setMaximumWidth(180)

        row2.addWidget(self.cli_address_input)
        row2.addWidget(self.cli_notes_input)
        row2.addWidget(self.cli_discount_input)
        form_layout.addLayout(row2)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_save = QPushButton("Guardar")
        btn_save.setFixedHeight(48)
        btn_save.setStyleSheet(BLUE)
        btn_save.clicked.connect(self.save_client)

        btn_update = QPushButton("Actualizar")
        btn_update.setFixedHeight(48)
        btn_update.setStyleSheet(BLUE)
        btn_update.clicked.connect(self.update_client)

        btn_delete = QPushButton("Eliminar")
        btn_delete.setFixedHeight(48)
        btn_delete.setStyleSheet(RED)
        btn_delete.clicked.connect(self.delete_client)

        btn_clear = QPushButton("Limpiar")
        btn_clear.setFixedHeight(48)
        btn_clear.setStyleSheet(BLUE)
        btn_clear.clicked.connect(self.clear_client_form)

        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_update)
        btn_row.addWidget(btn_delete)
        btn_row.addWidget(btn_clear)
        form_layout.addLayout(btn_row)

        layout.addWidget(form_frame)

        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(6)
        self.clients_table.setHorizontalHeaderLabels([
            "N° Cuenta", "Nombre", "Teléfono", "Email", "Dirección", "Descuento %"
        ])
        self.clients_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.clients_table.verticalHeader().setVisible(False)
        self.clients_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.clients_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.clients_table.setStyleSheet("""
            QTableWidget { background-color: white; border-radius: 16px; font-size: 14px; color: #1E293B; border: none; }
            QHeaderView::section { background-color: #4A6A92; color: white; padding: 12px; border: none; font-weight: bold; }
            QTableWidget::item { padding: 10px; }
            QTableWidget::item:selected { background-color: #DBEAFE; color: #1E293B; }
        """)
        self.clients_table.cellClicked.connect(self.select_client)
        layout.addWidget(self.clients_table)

        self.load_clients()
        return widget

    # ── Tab Cuenta Corriente ──────────────────────────

    def build_accounts_tab(self):

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(14)

        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: white; border-radius: 16px;")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(12)

        row1 = QHBoxLayout()
        self.acc_client_input = self.create_input("N° Cuenta o nombre del cliente *")
        self.acc_detail_input = self.create_input("Detalle de la compra")
        self.acc_amount_input = self.create_input("Importe *")
        row1.addWidget(self.acc_client_input)
        row1.addWidget(self.acc_detail_input)
        row1.addWidget(self.acc_amount_input)
        form_layout.addLayout(row1)

        row2 = QHBoxLayout()
        delivery_label = QLabel("Fecha entrega:")
        delivery_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        self.acc_delivery_date = QDateEdit()
        self.acc_delivery_date.setDate(QDate.currentDate())
        self.acc_delivery_date.setCalendarPopup(True)
        self.acc_delivery_date.setDisplayFormat("dd/MM/yyyy")
        self.acc_delivery_date.setStyleSheet(INPUT_STYLE)

        payment_label = QLabel("Fecha pago:")
        payment_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        self.acc_payment_date = QDateEdit()
        self.acc_payment_date.setDate(QDate.currentDate())
        self.acc_payment_date.setCalendarPopup(True)
        self.acc_payment_date.setDisplayFormat("dd/MM/yyyy")
        self.acc_payment_date.setStyleSheet(INPUT_STYLE)

        self.acc_paid_check = QCheckBox("Pagado")
        self.acc_paid_check.setStyleSheet("font-size: 14px; color: #1E293B; background: transparent;")

        self.acc_notes_input = self.create_input("Notas")

        row2.addWidget(delivery_label)
        row2.addWidget(self.acc_delivery_date)
        row2.addWidget(payment_label)
        row2.addWidget(self.acc_payment_date)
        row2.addWidget(self.acc_paid_check)
        row2.addWidget(self.acc_notes_input)
        form_layout.addLayout(row2)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_save = QPushButton("Guardar")
        btn_save.setFixedHeight(48)
        btn_save.setStyleSheet(BLUE)
        btn_save.clicked.connect(self.save_account)

        btn_paid = QPushButton("Marcar pagado")
        btn_paid.setFixedHeight(48)
        btn_paid.setStyleSheet(BLUE)
        btn_paid.clicked.connect(self.mark_account_paid)

        btn_delete = QPushButton("Eliminar")
        btn_delete.setFixedHeight(48)
        btn_delete.setStyleSheet(RED)
        btn_delete.clicked.connect(self.delete_account)

        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_paid)
        btn_row.addWidget(btn_delete)
        form_layout.addLayout(btn_row)

        layout.addWidget(form_frame)

        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(8)
        self.accounts_table.setHorizontalHeaderLabels([
            "ID", "Cliente", "N° Cuenta", "Detalle",
            "F. Entrega", "F. Pago", "Importe", "Estado"
        ])
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.accounts_table.verticalHeader().setVisible(False)
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.accounts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.accounts_table.setStyleSheet("""
            QTableWidget { background-color: white; border-radius: 16px; font-size: 14px; color: #1E293B; border: none; }
            QHeaderView::section { background-color: #4A6A92; color: white; padding: 12px; border: none; font-weight: bold; }
            QTableWidget::item { padding: 10px; }
            QTableWidget::item:selected { background-color: #DBEAFE; color: #1E293B; }
        """)
        layout.addWidget(self.accounts_table)

        self.load_accounts()
        return widget

    # ── Helpers ───────────────────────────────────────

    def create_input(self, placeholder):
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setMinimumHeight(44)
        field.setStyleSheet(INPUT_STYLE)
        return field

    # ── Lógica Clientes ───────────────────────────────

    def generate_account_number(self):
        db = SessionLocal()
        try:
            count = db.query(Client).count()
            return f"CC-{str(count + 1).zfill(5)}"
        finally:
            db.close()

    def load_clients(self):

        db = SessionLocal()
        try:
            clients = db.query(Client).filter(Client.is_active == True).all()
        finally:
            db.close()

        self.clients_table.setRowCount(0)
        for row, c in enumerate(clients):
            self.clients_table.insertRow(row)
            self.clients_table.setItem(row, 0, QTableWidgetItem(c.account_number or ""))
            self.clients_table.setItem(row, 1, QTableWidgetItem(c.name or ""))
            self.clients_table.setItem(row, 2, QTableWidgetItem(c.phone or ""))
            self.clients_table.setItem(row, 3, QTableWidgetItem(c.email or ""))
            self.clients_table.setItem(row, 4, QTableWidgetItem(c.address or ""))
            discount = c.discount or 0
            discount_item = QTableWidgetItem(f"{int(discount)}%" if discount > 0 else "Sin descuento")
            discount_item.setTextAlignment(Qt.AlignCenter)
            self.clients_table.setItem(row, 5, discount_item)

    def select_client(self, row):

        self.selected_client_id = None
        account_number = self.clients_table.item(row, 0).text()
        db = SessionLocal()
        try:
            client = db.query(Client).filter(Client.account_number == account_number).first()
            if client:
                self.selected_client_id = client.id
                self.cli_name_input.setText(client.name or "")
                self.cli_phone_input.setText(client.phone or "")
                self.cli_email_input.setText(client.email or "")
                self.cli_address_input.setText(client.address or "")
                self.cli_notes_input.setText(client.notes or "")
                discount = client.discount or 0
                self.cli_discount_input.setText(str(int(discount)) if discount > 0 else "")
        finally:
            db.close()

    def save_client(self):

        name = self.cli_name_input.text().strip().upper()
        if not name:
            self.show_message("Error", "El nombre es obligatorio")
            return

        try:
            discount = float(self.cli_discount_input.text().strip() or 0)
            if discount < 0 or discount > 100:
                self.show_message("Error", "El descuento debe ser entre 0 y 100")
                return
        except ValueError:
            self.show_message("Error", "El descuento debe ser un número")
            return

        db = SessionLocal()
        try:
            client = Client(
                account_number=self.generate_account_number(),
                name=name,
                phone=self.cli_phone_input.text().strip(),
                email=self.cli_email_input.text().strip(),
                address=self.cli_address_input.text().strip(),
                notes=self.cli_notes_input.text().strip(),
                discount=discount,
                is_active=True
            )
            db.add(client)
            db.commit()
            msg = f"Cliente guardado. N° Cuenta: {client.account_number}"
            if discount > 0:
                msg += f"\nDescuento aplicado: {int(discount)}%"
            self.show_message("OK", msg)
            self.load_clients()
            self.clear_client_form()
        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def update_client(self):

        if not self.selected_client_id:
            self.show_message("Error", "Seleccione un cliente")
            return

        try:
            discount = float(self.cli_discount_input.text().strip() or 0)
            if discount < 0 or discount > 100:
                self.show_message("Error", "El descuento debe ser entre 0 y 100")
                return
        except ValueError:
            self.show_message("Error", "El descuento debe ser un número")
            return

        db = SessionLocal()
        try:
            client = db.query(Client).filter(Client.id == self.selected_client_id).first()
            if not client:
                self.show_message("Error", "Cliente no encontrado")
                return
            client.name = self.cli_name_input.text().strip().upper()
            client.phone = self.cli_phone_input.text().strip()
            client.email = self.cli_email_input.text().strip()
            client.address = self.cli_address_input.text().strip()
            client.notes = self.cli_notes_input.text().strip()
            client.discount = discount
            db.commit()
            self.show_message("OK", "Cliente actualizado correctamente")
            self.load_clients()
            self.clear_client_form()
        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def delete_client(self):

        if not self.selected_client_id:
            self.show_message("Error", "Seleccione un cliente")
            return

        db = SessionLocal()
        try:
            client = db.query(Client).filter(Client.id == self.selected_client_id).first()
            if client:
                client.is_active = False
                db.commit()
            self.show_message("OK", "Cliente eliminado correctamente")
            self.load_clients()
            self.clear_client_form()
        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def clear_client_form(self):
        self.selected_client_id = None
        self.cli_name_input.clear()
        self.cli_phone_input.clear()
        self.cli_email_input.clear()
        self.cli_address_input.clear()
        self.cli_notes_input.clear()
        self.cli_discount_input.clear()

    # ── Lógica Cuenta Corriente ───────────────────────

    def load_accounts(self):

        db = SessionLocal()
        try:
            accounts = db.query(ClientAccount).order_by(ClientAccount.id.desc()).all()
            clients = {c.id: c for c in db.query(Client).all()}
        finally:
            db.close()

        self.accounts_table.setRowCount(0)
        for row, acc in enumerate(accounts):
            self.accounts_table.insertRow(row)
            client = clients.get(acc.client_id)
            client_name = client.name if client else ""
            account_number = client.account_number if client else ""

            self.accounts_table.setItem(row, 0, QTableWidgetItem(str(acc.id)))
            self.accounts_table.setItem(row, 1, QTableWidgetItem(client_name))
            self.accounts_table.setItem(row, 2, QTableWidgetItem(account_number))
            self.accounts_table.setItem(row, 3, QTableWidgetItem(acc.detail or ""))
            self.accounts_table.setItem(row, 4, QTableWidgetItem(
                acc.delivery_date.strftime("%d/%m/%Y") if acc.delivery_date else ""
            ))
            self.accounts_table.setItem(row, 5, QTableWidgetItem(
                acc.payment_date.strftime("%d/%m/%Y") if acc.payment_date else ""
            ))
            self.accounts_table.setItem(row, 6, QTableWidgetItem(f"$ {int(acc.amount or 0)}"))
            estado = "Pagado" if acc.is_paid else "Pendiente"
            estado_item = QTableWidgetItem(estado)
            estado_item.setForeground(Qt.darkGreen if acc.is_paid else Qt.red)
            self.accounts_table.setItem(row, 7, estado_item)

    def save_account(self):

        client_input = self.acc_client_input.text().strip()
        amount_text = self.acc_amount_input.text().strip()

        if not client_input or not amount_text:
            self.show_message("Error", "Cliente e importe son obligatorios")
            return

        db = SessionLocal()
        try:
            client = db.query(Client).filter(
                (Client.account_number == client_input) |
                (Client.name == client_input.upper()),
                Client.is_active == True
            ).first()

            if not client:
                self.show_message("Error", f"Cliente '{client_input}' no encontrado")
                return

            delivery_date = self.acc_delivery_date.date().toPython()
            payment_date = self.acc_payment_date.date().toPython()

            account = ClientAccount(
                client_id=client.id,
                account_number=client.account_number,
                detail=self.acc_detail_input.text().strip(),
                delivery_date=datetime.combine(delivery_date, datetime.min.time()),
                payment_date=datetime.combine(payment_date, datetime.min.time()),
                amount=float(amount_text),
                is_paid=self.acc_paid_check.isChecked(),
                notes=self.acc_notes_input.text().strip()
            )
            db.add(account)
            db.commit()
            self.show_message("OK", "Cuenta corriente guardada correctamente")
            self.load_accounts()
            self.clear_account_form()
        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def mark_account_paid(self):

        selected_row = self.accounts_table.currentRow()
        if selected_row < 0:
            self.show_message("Error", "Seleccione un registro")
            return

        account_id = int(self.accounts_table.item(selected_row, 0).text())

        db = SessionLocal()
        try:
            account = db.query(ClientAccount).filter(ClientAccount.id == account_id).first()
            if account:
                account.is_paid = True
                db.commit()
            self.show_message("OK", "Cuenta corriente marcada como pagada")
            self.load_accounts()
        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def delete_account(self):

        selected_row = self.accounts_table.currentRow()
        if selected_row < 0:
            self.show_message("Error", "Seleccione un registro")
            return

        account_id = int(self.accounts_table.item(selected_row, 0).text())

        db = SessionLocal()
        try:
            account = db.query(ClientAccount).filter(ClientAccount.id == account_id).first()
            if account:
                db.delete(account)
                db.commit()
            self.show_message("OK", "Registro eliminado")
            self.load_accounts()
        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def clear_account_form(self):
        self.acc_client_input.clear()
        self.acc_detail_input.clear()
        self.acc_amount_input.clear()
        self.acc_notes_input.clear()
        self.acc_delivery_date.setDate(QDate.currentDate())
        self.acc_payment_date.setDate(QDate.currentDate())
        self.acc_paid_check.setChecked(False)

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