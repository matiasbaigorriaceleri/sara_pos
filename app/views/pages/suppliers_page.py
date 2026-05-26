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
    QSizePolicy,
)

from PySide6.QtCore import Qt, QDate
from app.database.database import SessionLocal
from app.models.supplier_model import Supplier
from app.models.supplier_invoice_model import SupplierInvoice
from app.assets.themes.theme import PRIMARY_COLOR, BACKGROUND_COLOR, INPUT_STYLE
from datetime import datetime, date, timedelta

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

LABEL_STYLE = "font-size: 13px; color: #64748B; background: transparent; font-weight: bold;"
BLUE = "QPushButton { background-color: #4A6A92; color: white; border: none; border-radius: 12px; font-size: 15px; font-weight: bold; padding: 10px 16px; } QPushButton:hover { background-color: #3D5A80; }"
RED = "QPushButton { background-color: #FF003D; color: white; border: none; border-radius: 12px; font-size: 15px; font-weight: bold; padding: 10px 16px; } QPushButton:hover { background-color: #D90429; }"


class SuppliersPage(QWidget):

    def __init__(self):
        super().__init__()
        self.selected_supplier_id = None
        self.setup_ui()
        self.check_payment_alerts()

    def setup_ui(self):

        self.setStyleSheet(f"background-color: {BACKGROUND_COLOR};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        title = QLabel("Proveedores")
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

        tabs.addTab(self.build_suppliers_tab(), "ABM Proveedores")
        tabs.addTab(self.build_invoices_tab(), "Facturas / Remitos")

        main_layout.addWidget(tabs)

    # ── Tab ABM Proveedores ───────────────────────────

    def build_suppliers_tab(self):

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
        self.sup_name_input = self.create_input("Nombre proveedor *")
        self.sup_contact_input = self.create_input("Contacto")
        self.sup_phone_input = self.create_input("Teléfono")
        row1.addWidget(self.sup_name_input)
        row1.addWidget(self.sup_contact_input)
        row1.addWidget(self.sup_phone_input)
        form_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.sup_email_input = self.create_input("Email")
        self.sup_address_input = self.create_input("Dirección")
        self.sup_notes_input = self.create_input("Notas")
        row2.addWidget(self.sup_email_input)
        row2.addWidget(self.sup_address_input)
        row2.addWidget(self.sup_notes_input)
        form_layout.addLayout(row2)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_save = QPushButton("Guardar")
        btn_save.setFixedHeight(48)
        btn_save.setStyleSheet(BLUE)
        btn_save.clicked.connect(self.save_supplier)

        btn_update = QPushButton("Actualizar")
        btn_update.setFixedHeight(48)
        btn_update.setStyleSheet(BLUE)
        btn_update.clicked.connect(self.update_supplier)

        btn_delete = QPushButton("Eliminar")
        btn_delete.setFixedHeight(48)
        btn_delete.setStyleSheet(RED)
        btn_delete.clicked.connect(self.delete_supplier)

        btn_clear = QPushButton("Limpiar")
        btn_clear.setFixedHeight(48)
        btn_clear.setStyleSheet(BLUE)
        btn_clear.clicked.connect(self.clear_supplier_form)

        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_update)
        btn_row.addWidget(btn_delete)
        btn_row.addWidget(btn_clear)
        form_layout.addLayout(btn_row)

        layout.addWidget(form_frame)

        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(5)
        self.suppliers_table.setHorizontalHeaderLabels(["ID", "Nombre", "Contacto", "Teléfono", "Email"])
        self.suppliers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.suppliers_table.verticalHeader().setVisible(False)
        self.suppliers_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.suppliers_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.suppliers_table.setStyleSheet(self.table_style())
        self.suppliers_table.cellClicked.connect(self.select_supplier)
        layout.addWidget(self.suppliers_table)

        self.load_suppliers()
        return widget

    # ── Tab Facturas ──────────────────────────────────

    def build_invoices_tab(self):

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
        self.inv_supplier_input = self.create_input("Nombre proveedor *")
        self.inv_number_input = self.create_input("N° Remito / Factura")
        self.inv_amount_input = self.create_input("Monto *")
        row1.addWidget(self.inv_supplier_input)
        row1.addWidget(self.inv_number_input)
        row1.addWidget(self.inv_amount_input)
        form_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(12)
        row2.setAlignment(Qt.AlignVCenter)

        entry_label = QLabel("Fecha ingreso:")
        entry_label.setStyleSheet(LABEL_STYLE)
        entry_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.inv_entry_date = QDateEdit()
        self.inv_entry_date.setDate(QDate.currentDate())
        self.inv_entry_date.setCalendarPopup(True)
        self.inv_entry_date.setDisplayFormat("dd/MM/yyyy")
        self.inv_entry_date.setStyleSheet(DATE_STYLE)
        self.inv_entry_date.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        payment_label = QLabel("Fecha pago:")
        payment_label.setStyleSheet(LABEL_STYLE)
        payment_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.inv_payment_date = QDateEdit()
        self.inv_payment_date.setDate(QDate.currentDate())
        self.inv_payment_date.setCalendarPopup(True)
        self.inv_payment_date.setDisplayFormat("dd/MM/yyyy")
        self.inv_payment_date.setStyleSheet(DATE_STYLE)
        self.inv_payment_date.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.inv_paid_check = QCheckBox("Pagado")
        self.inv_paid_check.setStyleSheet("font-size: 14px; color: #1E293B; background: transparent;")

        self.inv_notes_input = self.create_input("Notas")

        row2.addWidget(entry_label)
        row2.addWidget(self.inv_entry_date)
        row2.addSpacing(8)
        row2.addWidget(payment_label)
        row2.addWidget(self.inv_payment_date)
        row2.addSpacing(8)
        row2.addWidget(self.inv_paid_check)
        row2.addWidget(self.inv_notes_input)
        form_layout.addLayout(row2)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_save = QPushButton("Guardar factura")
        btn_save.setFixedHeight(48)
        btn_save.setStyleSheet(BLUE)
        btn_save.clicked.connect(self.save_invoice)

        btn_mark_paid = QPushButton("Marcar pagado")
        btn_mark_paid.setFixedHeight(48)
        btn_mark_paid.setStyleSheet(BLUE)
        btn_mark_paid.clicked.connect(self.mark_invoice_paid)

        btn_delete = QPushButton("Eliminar")
        btn_delete.setFixedHeight(48)
        btn_delete.setStyleSheet(RED)
        btn_delete.clicked.connect(self.delete_invoice)

        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_mark_paid)
        btn_row.addWidget(btn_delete)
        form_layout.addLayout(btn_row)

        layout.addWidget(form_frame)

        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(7)
        self.invoices_table.setHorizontalHeaderLabels([
            "ID", "Proveedor", "N° Factura", "F. Ingreso", "F. Pago", "Monto", "Estado"
        ])
        self.invoices_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.invoices_table.verticalHeader().setVisible(False)
        self.invoices_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.invoices_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.invoices_table.setStyleSheet(self.table_style())
        layout.addWidget(self.invoices_table)

        self.load_invoices()
        return widget

    # ── Helpers ───────────────────────────────────────

    def create_input(self, placeholder):
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setMinimumHeight(44)
        field.setStyleSheet(INPUT_STYLE)
        return field

    def table_style(self):
        return """
            QTableWidget { background-color: white; border-radius: 16px; font-size: 14px; color: #1E293B; border: none; }
            QHeaderView::section { background-color: #4A6A92; color: white; padding: 12px; border: none; font-weight: bold; }
            QTableWidget::item { padding: 10px; }
            QTableWidget::item:selected { background-color: #DBEAFE; color: #1E293B; }
        """

    # ── Alertas de vencimiento ────────────────────────

    def check_payment_alerts(self):
        tomorrow = date.today() + timedelta(days=1)
        today = date.today()

        db = SessionLocal()
        try:
            invoices = db.query(SupplierInvoice).filter(SupplierInvoice.is_paid == False).all()
            suppliers = {s.id: s.name for s in db.query(Supplier).all()}
            alerts = []

            for inv in invoices:
                if inv.payment_date:
                    inv_date = inv.payment_date.date() if hasattr(inv.payment_date, 'date') else inv.payment_date
                    supplier_name = suppliers.get(inv.supplier_id, "Proveedor desconocido")
                    if inv_date == today:
                        alerts.append(f"• {supplier_name} — $ {int(inv.amount or 0)} — VENCE HOY")
                    elif inv_date == tomorrow:
                        alerts.append(f"• {supplier_name} — $ {int(inv.amount or 0)} — vence mañana")
        finally:
            db.close()

        if alerts:
            msg = QMessageBox(self)
            msg.setWindowTitle("⚠️ Alertas de pago a proveedores")
            msg.setText("Facturas que vencen hoy o mañana:\n\n" + "\n".join(alerts))
            msg.setStyleSheet("""
                QMessageBox { background-color: white; }
                QLabel { color: #1E293B; font-size: 14px; min-width: 380px; }
                QPushButton {
                    background-color: #4A6A92; color: white; border: none;
                    border-radius: 10px; padding: 10px 20px; min-width: 80px;
                    min-height: 32px; font-size: 13px; font-weight: bold;
                }
                QPushButton:hover { background-color: #3D5A80; }
            """)
            msg.exec()

    # ── Lógica Proveedores ────────────────────────────

    def load_suppliers(self):

        db = SessionLocal()
        try:
            suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
        finally:
            db.close()

        self.suppliers_table.setRowCount(0)
        for row, s in enumerate(suppliers):
            self.suppliers_table.insertRow(row)
            self.suppliers_table.setItem(row, 0, QTableWidgetItem(str(s.id)))
            self.suppliers_table.setItem(row, 1, QTableWidgetItem(s.name or ""))
            self.suppliers_table.setItem(row, 2, QTableWidgetItem(s.contact or ""))
            self.suppliers_table.setItem(row, 3, QTableWidgetItem(s.phone or ""))
            self.suppliers_table.setItem(row, 4, QTableWidgetItem(s.email or ""))

    def select_supplier(self, row):

        self.selected_supplier_id = int(self.suppliers_table.item(row, 0).text())
        self.sup_name_input.setText(self.suppliers_table.item(row, 1).text())
        self.sup_contact_input.setText(self.suppliers_table.item(row, 2).text())
        self.sup_phone_input.setText(self.suppliers_table.item(row, 3).text())
        self.sup_email_input.setText(self.suppliers_table.item(row, 4).text())

    def save_supplier(self):

        name = self.sup_name_input.text().strip().upper()
        if not name:
            self.show_message("Error", "El nombre es obligatorio")
            return

        db = SessionLocal()
        try:
            supplier = Supplier(
                name=name,
                contact=self.sup_contact_input.text().strip(),
                phone=self.sup_phone_input.text().strip(),
                email=self.sup_email_input.text().strip(),
                address=self.sup_address_input.text().strip(),
                notes=self.sup_notes_input.text().strip(),
                is_active=True
            )
            db.add(supplier)
            db.commit()
            self.show_message("OK", "Proveedor guardado correctamente")
            self.load_suppliers()
            self.clear_supplier_form()
        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def update_supplier(self):

        if not self.selected_supplier_id:
            self.show_message("Error", "Seleccione un proveedor")
            return

        db = SessionLocal()
        try:
            supplier = db.query(Supplier).filter(Supplier.id == self.selected_supplier_id).first()
            if not supplier:
                self.show_message("Error", "Proveedor no encontrado")
                return
            supplier.name = self.sup_name_input.text().strip().upper()
            supplier.contact = self.sup_contact_input.text().strip()
            supplier.phone = self.sup_phone_input.text().strip()
            supplier.email = self.sup_email_input.text().strip()
            supplier.address = self.sup_address_input.text().strip()
            supplier.notes = self.sup_notes_input.text().strip()
            db.commit()
            self.show_message("OK", "Proveedor actualizado correctamente")
            self.load_suppliers()
            self.clear_supplier_form()
        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def delete_supplier(self):

        if not self.selected_supplier_id:
            self.show_message("Error", "Seleccione un proveedor")
            return

        db = SessionLocal()
        try:
            supplier = db.query(Supplier).filter(Supplier.id == self.selected_supplier_id).first()
            if supplier:
                supplier.is_active = False
                db.commit()
            self.show_message("OK", "Proveedor eliminado correctamente")
            self.load_suppliers()
            self.clear_supplier_form()
        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def clear_supplier_form(self):
        self.selected_supplier_id = None
        self.sup_name_input.clear()
        self.sup_contact_input.clear()
        self.sup_phone_input.clear()
        self.sup_email_input.clear()
        self.sup_address_input.clear()
        self.sup_notes_input.clear()

    # ── Lógica Facturas ───────────────────────────────

    def load_invoices(self):

        db = SessionLocal()
        try:
            invoices = db.query(SupplierInvoice).order_by(SupplierInvoice.id.desc()).all()
            suppliers = {s.id: s.name for s in db.query(Supplier).all()}
        finally:
            db.close()

        self.invoices_table.setRowCount(0)
        for row, inv in enumerate(invoices):
            self.invoices_table.insertRow(row)
            self.invoices_table.setItem(row, 0, QTableWidgetItem(str(inv.id)))
            self.invoices_table.setItem(row, 1, QTableWidgetItem(suppliers.get(inv.supplier_id, "")))
            self.invoices_table.setItem(row, 2, QTableWidgetItem(inv.invoice_number or ""))
            self.invoices_table.setItem(row, 3, QTableWidgetItem(
                inv.entry_date.strftime("%d/%m/%Y") if inv.entry_date else ""
            ))
            self.invoices_table.setItem(row, 4, QTableWidgetItem(
                inv.payment_date.strftime("%d/%m/%Y") if inv.payment_date else ""
            ))
            self.invoices_table.setItem(row, 5, QTableWidgetItem(f"$ {int(inv.amount or 0)}"))
            estado = "Pagado" if inv.is_paid else "Pendiente"
            estado_item = QTableWidgetItem(estado)
            estado_item.setForeground(Qt.darkGreen if inv.is_paid else Qt.red)
            self.invoices_table.setItem(row, 6, estado_item)

    def save_invoice(self):

        supplier_name = self.inv_supplier_input.text().strip().upper()
        amount_text = self.inv_amount_input.text().strip()

        if not supplier_name or not amount_text:
            self.show_message("Error", "Proveedor y monto son obligatorios")
            return

        db = SessionLocal()
        try:
            supplier = db.query(Supplier).filter(
                Supplier.name == supplier_name,
                Supplier.is_active == True
            ).first()

            if not supplier:
                self.show_message("Error", f"Proveedor '{supplier_name}' no encontrado.\nAsegurate de darlo de alta primero.")
                return

            entry_date = self.inv_entry_date.date().toPython()
            payment_date = self.inv_payment_date.date().toPython()

            invoice = SupplierInvoice(
                supplier_id=supplier.id,
                invoice_number=self.inv_number_input.text().strip(),
                entry_date=datetime.combine(entry_date, datetime.min.time()),
                payment_date=datetime.combine(payment_date, datetime.min.time()),
                amount=float(amount_text),
                is_paid=self.inv_paid_check.isChecked(),
                notes=self.inv_notes_input.text().strip()
            )
            db.add(invoice)
            db.commit()
            self.show_message("OK", "Factura guardada correctamente")
            self.load_invoices()
            self.clear_invoice_form()
        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def mark_invoice_paid(self):

        selected_row = self.invoices_table.currentRow()
        if selected_row < 0:
            self.show_message("Error", "Seleccione una factura")
            return

        invoice_id = int(self.invoices_table.item(selected_row, 0).text())

        db = SessionLocal()
        try:
            invoice = db.query(SupplierInvoice).filter(SupplierInvoice.id == invoice_id).first()
            if not invoice:
                self.show_message("Error", "Factura no encontrada")
                return

            if invoice.is_paid:
                self.show_message("Aviso", "Esta factura ya estaba pagada")
                return

            invoice.is_paid = True

            # ── Registrar egreso en caja abierta ──────
            from app.models.cash_session_model import CashSession
            from app.models.cash_movement_model import CashMovement

            cash_session = db.query(CashSession).filter(CashSession.is_open == True).first()

            supplier_name = self.invoices_table.item(selected_row, 1).text()
            invoice_number = self.invoices_table.item(selected_row, 2).text()
            concept = f"Pago a proveedor: {supplier_name}"
            if invoice_number:
                concept += f" — Factura {invoice_number}"

            if cash_session:
                movement = CashMovement(
                    cash_session_id=cash_session.id,
                    type="egreso",
                    concept=concept,
                    amount=invoice.amount or 0,
                )
                db.add(movement)
                msg = f"Factura marcada como pagada\nEgreso de $ {int(invoice.amount or 0)} registrado en caja"
            else:
                msg = f"Factura marcada como pagada\n⚠️ No hay caja abierta — el egreso no se registró en caja"

            db.commit()
            self.show_message("OK", msg)
            self.load_invoices()

        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def delete_invoice(self):

        selected_row = self.invoices_table.currentRow()
        if selected_row < 0:
            self.show_message("Error", "Seleccione una factura")
            return

        invoice_id = int(self.invoices_table.item(selected_row, 0).text())

        db = SessionLocal()
        try:
            invoice = db.query(SupplierInvoice).filter(SupplierInvoice.id == invoice_id).first()
            if invoice:
                db.delete(invoice)
                db.commit()
            self.show_message("OK", "Factura eliminada")
            self.load_invoices()
        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def clear_invoice_form(self):
        self.inv_supplier_input.clear()
        self.inv_number_input.clear()
        self.inv_amount_input.clear()
        self.inv_notes_input.clear()
        self.inv_entry_date.setDate(QDate.currentDate())
        self.inv_payment_date.setDate(QDate.currentDate())
        self.inv_paid_check.setChecked(False)

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