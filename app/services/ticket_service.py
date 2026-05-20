from datetime import datetime

from pathlib import Path

import subprocess

from app.database.database import SessionLocal

from app.models.settings_model import (
    Setting
)


class TicketService:

    @staticmethod
    def get_setting(key):

        db = SessionLocal()

        setting = db.query(Setting).filter(
            Setting.key == key
        ).first()

        db.close()

        if setting:
            return setting.value

        return ""

    # =====================================
    # GENERATE TICKET TEXT
    # =====================================

    @staticmethod
    def generate_ticket_text(
        cart,
        total,
        username
    ):

        business_name = (
            TicketService.get_setting(
                "business_name"
            )
        )

        business_cuit = (
            TicketService.get_setting(
                "business_cuit"
            )
        )

        business_address = (
            TicketService.get_setting(
                "business_address"
            )
        )

        business_phone = (
            TicketService.get_setting(
                "business_phone"
            )
        )

        footer = (
            TicketService.get_setting(
                "ticket_footer"
            )
        )

        now = datetime.now()

        ticket = ""

        # =====================================
        # HEADER
        # =====================================

        ticket += f"{business_name}\n"

        ticket += f"CUIT: {business_cuit}\n"

        ticket += f"{business_address}\n"

        ticket += f"TEL: {business_phone}\n"

        ticket += "-" * 40 + "\n"

        ticket += (
            f"Fecha: "
            f"{now.strftime('%d/%m/%Y %H:%M')}\n"
        )

        ticket += (
            f"Cajero: {username}\n"
        )

        ticket += "-" * 40 + "\n"

        # =====================================
        # PRODUCTS
        # =====================================

        for product_name, data in cart.items():

            quantity = data["quantity"]

            price = data["price"]

            subtotal = quantity * price

            ticket += (
                f"{product_name}\n"
            )

            ticket += (
                f"{quantity} x $ {price}"
                f"     $ {subtotal}\n"
            )

        ticket += "-" * 40 + "\n"

        # =====================================
        # TOTAL
        # =====================================

        ticket += (
            f"TOTAL: $ {total}\n"
        )

        ticket += "-" * 40 + "\n"

        # =====================================
        # FOOTER
        # =====================================

        ticket += f"{footer}\n"

        return ticket

    # =====================================
    # SAVE TICKET FILE
    # =====================================

    @staticmethod
    def save_ticket_file(ticket_text):

        tickets_folder = Path("tickets")

        tickets_folder.mkdir(
            exist_ok=True
        )

        filename = (
            "ticket_"
            + datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )
            + ".txt"
        )

        file_path = (
            tickets_folder / filename
        )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(ticket_text)

        return str(file_path)

    # =====================================
    # PRINT TICKET
    # =====================================

    @staticmethod
    def print_ticket(file_path):

        printer_name = (
            TicketService.get_setting(
                "printer_name"
            )
        )

        try:

            if printer_name:

                subprocess.run([
                    "lp",
                    "-d",
                    printer_name,
                    file_path
                ])

            else:

                subprocess.run([
                    "lp",
                    file_path
                ])

            return True

        except Exception as error:

            print(
                "Error impresión:",
                error
            )

            return False
