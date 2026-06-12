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
    QLineEdit,
    QTextEdit,
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

import bcrypt
from datetime import datetime, timedelta

from app.assets.themes.theme import PRIMARY_COLOR
from app.database.database import SessionLocal
from app.models.ticket_model import Ticket
from app.models.ticket_item_model import TicketItem
from app.models.product_model import Product
from app.models.user_model import User


# ── Diálogo de autorización de admin ─────────────────

class AdminAuthDialog(QDialog):
    """Pide usuario y contraseña de ADMIN para autorizar operaciones sensibles."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Autorización requerida")
        self.setMinimumWidth(380)
        self.setStyleSheet("background-color: white;")
        self.authorized_user = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("🔐  Se requiere autorización de ADMIN")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E293B;")
        title.setWordWrap(True)
        layout.addWidget(title)

        subtitle = QLabel("Ingresá usuario y contraseña de administrador para continuar.")
        subtitle.setStyleSheet("font-size: 12px; color: #64748B;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        input_style = """
            QLineEdit {
                background-color: white;
                border: 2px solid #B8C4D0;
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 14px;
                color: #1E293B;
            }
            QLineEdit:focus { border: 2px solid #4A6A92; }
        """

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Usuario administrador")
        self.user_input.setMinimumHeight(46)
        self.user_input.setStyleSheet(input_style)
        layout.addWidget(self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Contraseña")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setMinimumHeight(46)
        self.pass_input.setStyleSheet(input_style)
        self.pass_input.returnPressed.connect(self._verify)
        layout.addWidget(self.pass_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("font-size: 12px; color: #EF4444;")
        layout.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setFixedHeight(44)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #4A6A92;
                border: 2px solid #4A6A92;
                border-radius: 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #EFF6FF; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("Autorizar")
        btn_ok.setFixedHeight(44)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #4A6A92;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3D5A80; }
        """)
        btn_ok.clicked.connect(self._verify)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _verify(self):
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()

        if not username or not password:
            self.error_label.setText("Completá usuario y contraseña.")
            return

        db = SessionLocal()
        try:
            user = db.query(User).filter(
                User.username == username,
                User.role == "ADMIN",
                User.is_active == True
            ).first()

            if not user:
                self.error_label.setText("Usuario no encontrado o no es administrador.")
                return

            try:
                ok = bcrypt.checkpw(
                    password.encode("utf-8"),
                    user.password.encode("utf-8")
                )
            except Exception:
                ok = False

            if not ok:
                self.error_label.setText("Contraseña incorrecta.")
                return

            self.authorized_user = username
            self.accept()

        finally:
            db.close()


# ── Diálogo de motivo de anulación ───────────────────

class CancelReasonDialog(QDialog):

    def __init__(self, ticket_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Anular venta")
        self.setMinimumWidth(400)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel(f"Anular Ticket #{ticket_id:05d}")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #EF4444;")
        layout.addWidget(title)

        warning = QLabel("⚠️  Esta acción devolverá el stock de todos los productos y marcará la venta como ANULADA. No se puede deshacer.")
        warning.setStyleSheet("font-size: 12px; color: #64748B; background: #FEF2F2; border-radius: 8px; padding: 8px;")
        warning.setWordWrap(True)
        layout.addWidget(warning)

        reason_label = QLabel("Motivo de anulación (obligatorio):")
        reason_label.setStyleSheet("font-size: 13px; color: #1E293B;")
        layout.addWidget(reason_label)

        self.reason_input = QTextEdit()
        self.reason_input.setPlaceholderText("Ej: Cliente se arrepintió, error en el precio, etc.")
        self.reason_input.setMaximumHeight(80)
        self.reason_input.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 2px solid #B8C4D0;
                border-radius: 10px;
                padding: 8px;
                font-size: 13px;
                color: #1E293B;
            }
        """)
        layout.addWidget(self.reason_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("font-size: 12px; color: #EF4444;")
        layout.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setFixedHeight(44)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #4A6A92;
                border: 2px solid #4A6A92;
                border-radius: 10px;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_confirm = QPushButton("Confirmar anulación")
        btn_confirm.setFixedHeight(44)
        btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #DC2626; }
        """)
        btn_confirm.clicked.connect(self._confirm)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_confirm)
        layout.addLayout(btn_row)

    def _confirm(self):
        reason = self.reason_input.toPlainText().strip()
        if not reason:
            self.error_label.setText("El motivo es obligatorio.")
            return
        self.accept()

    def get_reason(self):
        return self.reason_input.toPlainText().strip()


# ── Página principal ──────────────────────────────────

class SalesDetailPage(QWidget):

    def __init__(self, current_user=None, current_role=None):
        super().__init__()
        self.current_user = current_user or "admin"
        self.current_role = current_role or "ADMIN"
        self.all_tickets = []

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        title = QLabel("Detalle de Ventas")
        title.setStyleSheet(f"font-size: 34px; font-weight: bold; color: {PRIMARY_COLOR};")
        main_layout.addWidget(title)

        filter_frame = QFrame()
        filter_frame.setStyleSheet("QFrame { background-color: white; border-radius: 12px; padding: 4px; }")
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
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4A6A92;")
        filter_layout.addWidget(self.total_label)

        main_layout.addWidget(filter_frame)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "N° Ticket", "Fecha", "Usuario", "Método pago", "Total", "Estado", "Acciones"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 220)
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

    def set_user(self, username, role):
        self.current_user = username
        self.current_role = role

    def create_filter_button(self, text, active=False):
        btn = QPushButton(text)
        btn.setMinimumHeight(36)
        btn.setCursor(Qt.PointingHandCursor)
        if active:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4A6A92; color: white;
                    border: none; border-radius: 8px;
                    padding: 6px 16px; font-size: 13px; font-weight: bold;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #F1F5F9; color: #4A6A92;
                    border: 1px solid #B8C4D0; border-radius: 8px;
                    padding: 6px 16px; font-size: 13px; font-weight: bold;
                }
                QPushButton:hover { background-color: #D8E6F5; }
            """)
        return btn

    def load_tickets(self):
        db = SessionLocal()
        try:
            self.all_tickets = db.query(Ticket).order_by(Ticket.id.desc()).all()
        finally:
            db.close()
        self.render_tickets(self.all_tickets)

    def filter_by(self, period):
        now = datetime.now()
        if period == "hoy":
            filtered = [t for t in self.all_tickets if t.created_at.date() == now.date()]
        elif period == "semana":
            filtered = [t for t in self.all_tickets if t.created_at >= now - timedelta(days=7)]
        elif period == "mes":
            filtered = [t for t in self.all_tickets if t.created_at >= now - timedelta(days=30)]
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
            is_cancelled = (getattr(ticket, "status", "active") == "cancelled")

            if not is_cancelled:
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

            # Estado
            if is_cancelled:
                status_item = QTableWidgetItem("ANULADO")
                status_item.setForeground(QColor("#EF4444"))
                status_item.setFont(self.table.font())
            else:
                status_item = QTableWidgetItem("Activo")
                status_item.setForeground(QColor("#16A34A"))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, status_item)

            # Acciones
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(6)

            btn_detail = QPushButton("Ver detalle")
            btn_detail.setStyleSheet("""
                QPushButton {
                    background-color: #4A6A92; color: white;
                    border: none; border-radius: 6px;
                    padding: 5px 10px; font-size: 11px; font-weight: bold;
                }
                QPushButton:hover { background-color: #3D5A80; }
            """)
            btn_detail.setCursor(Qt.PointingHandCursor)
            btn_detail.clicked.connect(lambda checked, t=ticket: self.show_ticket_detail(t))
            btn_layout.addWidget(btn_detail)

            # Botón anular — solo si no está ya anulado
            if not is_cancelled:
                btn_cancel = QPushButton("Anular")
                btn_cancel.setStyleSheet("""
                    QPushButton {
                        background-color: #EF4444; color: white;
                        border: none; border-radius: 6px;
                        padding: 5px 10px; font-size: 11px; font-weight: bold;
                    }
                    QPushButton:hover { background-color: #DC2626; }
                """)
                btn_cancel.setCursor(Qt.PointingHandCursor)
                btn_cancel.clicked.connect(lambda checked, t=ticket: self.cancel_ticket(t))
                btn_layout.addWidget(btn_cancel)

            self.table.setCellWidget(row, 6, btn_widget)

            # Fila anulada en gris
            if is_cancelled:
                for col in range(6):
                    item = self.table.item(row, col)
                    if item:
                        item.setForeground(QColor("#94A3B8"))

        self.total_label.setText(f"Total: $ {int(total_sum)}")

    def cancel_ticket(self, ticket):
        """Anula una venta — pide auth de admin si el usuario actual no lo es."""

        authorized_by = self.current_user

        # Si no es admin → pedir autorización
        if self.current_role != "ADMIN":
            auth_dialog = AdminAuthDialog(parent=self)
            if auth_dialog.exec() != QDialog.Accepted:
                return
            authorized_by = auth_dialog.authorized_user

        # Pedir motivo
        reason_dialog = CancelReasonDialog(ticket.id, parent=self)
        if reason_dialog.exec() != QDialog.Accepted:
            return

        reason = reason_dialog.get_reason()

        # Ejecutar anulación
        db = SessionLocal()
        try:
            db_ticket = db.query(Ticket).filter(Ticket.id == ticket.id).first()
            if not db_ticket:
                self._show_message("Error", "Ticket no encontrado")
                return

            if getattr(db_ticket, "status", "active") == "cancelled":
                self._show_message("Aviso", "Este ticket ya fue anulado.")
                return

            # Devolver stock
            items = db.query(TicketItem).filter(TicketItem.ticket_id == ticket.id).all()
            for item in items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    product.stock += item.quantity

            # Marcar como anulado
            db_ticket.status = "cancelled"
            db_ticket.cancel_reason = reason
            db_ticket.cancelled_by = authorized_by
            db_ticket.cancelled_at = datetime.now()

            db.commit()

            self._show_message(
                "✅ Venta anulada",
                f"Ticket #{ticket.id:05d} anulado correctamente.\n"
                f"Stock devuelto a inventario.\n"
                f"Autorizado por: {authorized_by}"
            )
            self.load_tickets()

        except Exception as e:
            db.rollback()
            self._show_message("Error", f"No se pudo anular: {str(e)}")
        finally:
            db.close()

    def show_ticket_detail(self, ticket):
        db = SessionLocal()
        try:
            items = db.query(TicketItem).filter(TicketItem.ticket_id == ticket.id).all()
            detail_lines = []
            for item in items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                name = product.name if product else f"Producto #{item.product_id}"
                detail_lines.append(f"• {name}  x{int(item.quantity)}  →  $ {int(item.subtotal)}")
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

        status = getattr(ticket, "status", "active")
        status_text = "⛔ ANULADO" if status == "cancelled" else "✅ Activo"

        cancel_info = ""
        if status == "cancelled":
            cancelled_by = getattr(ticket, "cancelled_by", "")
            cancel_reason = getattr(ticket, "cancel_reason", "")
            cancelled_at = getattr(ticket, "cancelled_at", None)
            cancelled_at_str = cancelled_at.strftime("%d/%m/%Y %H:%M") if cancelled_at else ""
            cancel_info = (
                f"\n─────────────────────\n"
                f"Anulado por: {cancelled_by}\n"
                f"Fecha anulación: {cancelled_at_str}\n"
                f"Motivo: {cancel_reason}"
            )

        msg = QMessageBox(self)
        msg.setWindowTitle(f"Ticket #{ticket.id:05d}")
        msg.setText(
            f"Estado: {status_text}\n"
            f"Fecha: {fecha}\n"
            f"Usuario: {ticket.username}\n"
            f"Método: {method}\n"
            f"─────────────────────\n"
            f"{detail_text}\n"
            f"─────────────────────\n"
            f"TOTAL: $ {int(ticket.total or 0)}"
            f"{cancel_info}"
        )
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1E293B; font-size: 14px; min-width: 340px; }
            QPushButton {
                background-color: #4A6A92; color: white; border: none;
                border-radius: 10px; padding: 10px 20px;
                min-width: 80px; min-height: 32px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #3D5A80; }
        """)
        msg.exec()

    def _show_message(self, title, message):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1E293B; font-size: 14px; min-width: 320px; }
            QPushButton {
                background-color: #4A6A92; color: white; border: none;
                border-radius: 10px; padding: 10px 20px;
                min-width: 80px; min-height: 32px; font-size: 13px; font-weight: bold;
            }
        """)
        msg.exec()

    def load_sales(self):
        self.load_tickets()