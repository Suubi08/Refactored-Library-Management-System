from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Button, Input, Label, Static
from ui.custom import BaseModal

import database as db

class CreateBorrowerModal(BaseModal):

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static("Enter Borrower Information", id="modal-title")

            with Vertical(classes="form-content"):
                with Vertical(classes="input-field"):
                    yield Label("Name:")
                    yield Input(placeholder="Enter full name", id="name_input")

                with Vertical(classes="input-field"):
                    yield Label("SSN:")
                    yield Input(placeholder="XXX-XX-XXXX", id="ssn_input")

                with Vertical(classes="input-field"):
                    yield Label("Address:")
                    yield Input(placeholder="Enter address", id="address_input")

                with Vertical(classes="input-field"):
                    yield Label("Phone:")
                    yield Input(placeholder="(XXX) XXX-XXXX", id="phone_input")

            with Horizontal(classes="form-buttons"):
                yield Button("Submit", variant="primary", id="submit_btn")
                yield Button("Cancel", variant="default", id="cancel_btn")

    @on(Button.Pressed)
    def handle_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit_btn":
            name = self.query_one("#name_input", Input).value.strip()
            ssn = self.query_one("#ssn_input", Input).value.strip()
            address = self.query_one("#address_input", Input).value.strip()
            phone = self.query_one("#phone_input", Input).value.strip()

            result = db.create_borrower(name, ssn, address, phone)

            if result.status:
                self.notify(result.message, severity="information")
                self.dismiss()
            else:
                self.notify(result.message, severity="error")

        elif event.button.id == "cancel_btn":
            self.dismiss()
