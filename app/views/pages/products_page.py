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
    QFileDialog,
)

from app.database.database import SessionLocal
from app.models.product_model import Product

from app.assets.themes.theme import (
    PRIMARY_COLOR,
    BACKGROUND_COLOR,
    INPUT_STYLE,
)


class ProductsPage(QWidget):

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_products()

    def setup_ui(self):

        self.setStyleSheet(f"background-color: {BACKGROUND_COLOR};")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        title = QLabel("Productos")
        title.setStyleSheet(f"""
            font-size: 34px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        """)
        main_layout.addWidget(title)

        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: white; border-radius: 22px;")

        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(14)

        row1 = QHBoxLayout()
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Código")
        self.code_input.setReadOnly(True)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre")
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Barcode")
        self.code_input.setStyleSheet(INPUT_STYLE)
        self.name_input.setStyleSheet(INPUT_STYLE)
        self.barcode_input.setStyleSheet(INPUT_STYLE)
        row1.addWidget(self.code_input)
        row1.addWidget(self.name_input)
        row1.addWidget(self.barcode_input)
        form_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.detail_input = QLineEdit()
        self.detail_input.setPlaceholderText("Detalle")
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Categoría")
        self.detail_input.setStyleSheet(INPUT_STYLE)
        self.category_input.setStyleSheet(INPUT_STYLE)
        row2.addWidget(self.detail_input)
        row2.addWidget(self.category_input)
        form_layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.stock_input = QLineEdit()
        self.stock_input.setPlaceholderText("Stock")
        self.minimum_stock_input = QLineEdit()
        self.minimum_stock_input.setPlaceholderText("Stock mínimo")
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Precio venta")
        self.cost_input = QLineEdit()
        self.cost_input.setPlaceholderText("Precio costo")
        self.stock_input.setStyleSheet(INPUT_STYLE)
        self.minimum_stock_input.setStyleSheet(INPUT_STYLE)
        self.price_input.setStyleSheet(INPUT_STYLE)
        self.cost_input.setStyleSheet(INPUT_STYLE)
        row3.addWidget(self.stock_input)
        row3.addWidget(self.minimum_stock_input)
        row3.addWidget(self.price_input)
        row3.addWidget(self.cost_input)
        form_layout.addLayout(row3)

        BUTTON_STYLE_BLUE = """
        QPushButton {
            background-color: #4A6A92;
            color: white;
            border: none;
            border-radius: 14px;
            font-size: 18px;
            font-weight: bold;
        }
        QPushButton:hover { background-color: #3D5A80; }
        """

        BUTTON_STYLE_RED = """
        QPushButton {
            background-color: #FF003D;
            color: white;
            border: none;
            border-radius: 14px;
            font-size: 18px;
            font-weight: bold;
        }
        QPushButton:hover { background-color: #D90429; }
        """

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        self.save_button = QPushButton("Guardar")
        self.save_button.setFixedHeight(60)
        self.save_button.setStyleSheet(BUTTON_STYLE_BLUE)
        self.save_button.clicked.connect(self.save_product)

        self.update_button = QPushButton("Actualizar")
        self.update_button.setFixedHeight(60)
        self.update_button.setStyleSheet(BUTTON_STYLE_BLUE)
        self.update_button.clicked.connect(self.update_product)

        self.delete_button = QPushButton("Eliminar")
        self.delete_button.setFixedHeight(60)
        self.delete_button.setStyleSheet(BUTTON_STYLE_RED)
        self.delete_button.clicked.connect(self.delete_product)

        self.import_button = QPushButton("Importar")
        self.import_button.setFixedHeight(60)
        self.import_button.setStyleSheet(BUTTON_STYLE_BLUE)
        self.import_button.clicked.connect(self.import_products)

        self.export_button = QPushButton("Exportar")
        self.export_button.setFixedHeight(60)
        self.export_button.setStyleSheet(BUTTON_STYLE_BLUE)
        self.export_button.clicked.connect(self.export_products)

        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.update_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.import_button)
        buttons_layout.addWidget(self.export_button)

        form_layout.addLayout(buttons_layout)
        form_frame.setLayout(form_layout)
        main_layout.addWidget(form_frame)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Código", "Nombre", "Barcode", "Stock", "Precio", "Categoría"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 18px;
                font-size: 15px;
                color: #1E293B;
                border: none;
            }
            QHeaderView::section {
                background-color: #4A6A92;
                color: white;
                padding: 14px;
                border: none;
                font-size: 15px;
                font-weight: bold;
            }
            QTableWidget::item { padding: 12px; }
            QTableWidget::item:selected {
                background-color: #DBEAFE;
                color: #1E293B;
            }
        """)
        self.table.cellClicked.connect(self.select_product)
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

    def generate_next_code(self):
        db = SessionLocal()
        try:
            all_products = db.query(Product).all()
            max_code = 0
            for product in all_products:
                try:
                    current_code = int(product.product_code)
                    if current_code > max_code:
                        max_code = current_code
                except:
                    pass
        finally:
            db.close()

        self.code_input.setText(str(max_code + 1).zfill(3))

    def load_products(self):

        db = SessionLocal()
        try:
            products = db.query(Product).filter(Product.is_active == True).all()
        finally:
            db.close()

        self.table.setRowCount(0)
        for row, product in enumerate(products):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(product.product_code)))
            self.table.setItem(row, 1, QTableWidgetItem(str(product.name)))
            self.table.setItem(row, 2, QTableWidgetItem(str(product.barcode)))
            self.table.setItem(row, 3, QTableWidgetItem(str(product.stock)))
            self.table.setItem(row, 4, QTableWidgetItem(str(product.price)))
            self.table.setItem(row, 5, QTableWidgetItem(str(product.category)))

        self.generate_next_code()

    def save_product(self):

        db = SessionLocal()
        try:
            name = self.name_input.text().strip().upper()
            detail = self.detail_input.text().strip().upper()
            barcode = self.barcode_input.text().strip()
            category = self.category_input.text().strip().upper()

            if not name:
                self.show_message("Error", "El nombre es obligatorio")
                return

            if not barcode.isdigit():
                self.show_message("Error", "El barcode solo acepta números")
                return

            existing_name = db.query(Product).filter(
                Product.name == name, Product.is_active == True
            ).first()
            if existing_name:
                self.show_message("Error", "Ya existe un producto con ese nombre")
                return

            existing_barcode = db.query(Product).filter(
                Product.barcode == barcode, Product.is_active == True
            ).first()
            if existing_barcode:
                self.show_message("Error", "Ya existe un producto con ese barcode")
                return

            product = Product(
                product_code=self.code_input.text(),
                name=name,
                detail=detail,
                barcode=barcode,
                stock=int(self.stock_input.text() or 0),
                minimum_stock=int(self.minimum_stock_input.text() or 0),
                price=float(self.price_input.text() or 0),
                cost_price=float(self.cost_input.text() or 0),
                category=category,
                is_active=True
            )
            db.add(product)
            db.commit()
            self.show_message("OK", "Producto guardado correctamente")
            self.load_products()
            self.clear_form()

        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def update_product(self):

        selected_row = self.table.currentRow()
        if selected_row < 0:
            self.show_message("Error", "Seleccione un producto")
            return

        product_code = self.table.item(selected_row, 0).text()
        db = SessionLocal()

        try:
            product = db.query(Product).filter(Product.product_code == product_code).first()
            if not product:
                self.show_message("Error", "Producto no encontrado")
                return

            product.name = self.name_input.text().strip().upper()
            product.detail = self.detail_input.text().strip().upper()
            product.barcode = self.barcode_input.text().strip()
            product.stock = int(self.stock_input.text() or 0)
            product.minimum_stock = int(self.minimum_stock_input.text() or 0)
            product.price = float(self.price_input.text() or 0)
            product.cost_price = float(self.cost_input.text() or 0)
            product.category = self.category_input.text().strip().upper()

            db.commit()
            self.show_message("OK", "Producto actualizado correctamente")
            self.load_products()
            self.clear_form()

        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def delete_product(self):

        selected_row = self.table.currentRow()
        if selected_row < 0:
            self.show_message("Error", "Seleccione un producto")
            return

        product_code = self.table.item(selected_row, 0).text()

        msg = QMessageBox(self)
        msg.setWindowTitle("Confirmar eliminación")
        msg.setText("¿Seguro que desea eliminar este producto?")
        msg.setIcon(QMessageBox.Question)
        yes_button = msg.addButton("Sí", QMessageBox.YesRole)
        msg.addButton("No", QMessageBox.NoRole)
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1E293B; font-size: 16px; font-weight: bold; min-width: 320px; }
            QPushButton {
                background-color: #4A6A92; color: white; border: none;
                border-radius: 10px; padding: 10px 20px; min-width: 100px;
                min-height: 36px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #3D5A80; }
        """)
        msg.exec()

        if msg.clickedButton() != yes_button:
            return

        db = SessionLocal()
        try:
            product = db.query(Product).filter(Product.product_code == product_code).first()
            if not product:
                self.show_message("Error", "Producto no encontrado")
                return
            product.is_active = False
            db.commit()
            self.show_message("OK", "Producto eliminado correctamente")
            self.load_products()
            self.clear_form()
        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def import_products(self):

        import pandas as pd  # ← importado solo cuando se necesita

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo", "", "Excel Files (*.xlsx *.xls)"
        )
        if not file_path:
            return

        db = SessionLocal()
        try:
            df = pd.read_excel(file_path, dtype=str)

            existing_names = set(p.name for p in db.query(Product.name).all())
            existing_barcodes = set(p.barcode for p in db.query(Product.barcode).all())

            all_codes = db.query(Product.product_code).all()
            max_code = 0
            for (code,) in all_codes:
                try:
                    val = int(code)
                    if val > max_code:
                        max_code = val
                except:
                    pass

            imported = 0
            skipped = 0
            products_to_add = []

            for _, row in df.iterrows():
                name = str(row.get("nombre", "")).strip().upper()
                detail = str(row.get("detalle", "")).strip().upper()
                barcode = str(row.get("barcode", "")).strip()
                category = str(row.get("categoria", "")).strip().upper()

                if not name or not barcode.isdigit():
                    skipped += 1
                    continue

                if name in existing_names or barcode in existing_barcodes:
                    skipped += 1
                    continue

                max_code += 1
                product = Product(
                    product_code=str(max_code).zfill(3),
                    name=name,
                    detail=detail,
                    barcode=barcode,
                    stock=int(float(row.get("stock", 0) or 0)),
                    minimum_stock=int(float(row.get("stock_minimo", 0) or 0)),
                    price=float(row.get("precio_venta", 0) or 0),
                    cost_price=float(row.get("precio_costo", 0) or 0),
                    category=category,
                    is_active=True
                )
                products_to_add.append(product)
                existing_names.add(name)
                existing_barcodes.add(barcode)
                imported += 1

            if products_to_add:
                db.add_all(products_to_add)
                db.commit()

            self.load_products()
            self.clear_form()
            self.show_message("OK", f"Importados: {imported} | Omitidos: {skipped}")

        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def export_products(self):

        import pandas as pd  # ← importado solo cuando se necesita

        db = SessionLocal()
        try:
            products = db.query(Product).filter(Product.is_active == True).all()
            data = [{
                "codigo": p.product_code,
                "nombre": p.name,
                "detalle": p.detail,
                "barcode": p.barcode,
                "stock": p.stock,
                "stock_minimo": p.minimum_stock,
                "precio_venta": p.price,
                "precio_costo": p.cost_price,
                "categoria": p.category,
            } for p in products]

            df = pd.DataFrame(data)

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar archivo", "productos_exportados.xlsx", "Excel Files (*.xlsx)"
            )
            if not file_path:
                return

            df.to_excel(file_path, index=False)
            self.show_message("OK", "Productos exportados correctamente")

        except Exception as e:
            self.show_message("Error", str(e))
        finally:
            db.close()

    def select_product(self, row):
        self.code_input.setText(self.table.item(row, 0).text())
        self.name_input.setText(self.table.item(row, 1).text())
        self.barcode_input.setText(self.table.item(row, 2).text())
        self.stock_input.setText(self.table.item(row, 3).text())
        self.price_input.setText(self.table.item(row, 4).text())
        self.category_input.setText(self.table.item(row, 5).text())

    def clear_form(self):
        self.name_input.clear()
        self.detail_input.clear()
        self.barcode_input.clear()
        self.stock_input.clear()
        self.minimum_stock_input.clear()
        self.price_input.clear()
        self.cost_input.clear()
        self.category_input.clear()
        self.generate_next_code()

    def show_message(self, title, message):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1E293B; font-size: 16px; font-weight: bold; min-width: 300px; }
            QPushButton {
                background-color: #4A6A92; color: white; border: none;
                border-radius: 10px; padding: 10px 20px; min-width: 90px;
                min-height: 35px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #3D5A80; }
        """)
        msg.exec()