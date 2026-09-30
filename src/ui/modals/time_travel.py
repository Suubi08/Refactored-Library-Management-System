from datetime import date, timedelta

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Button, Label, Static

from ui.custom import BaseModal

import database as db

class TimeTravelModal(BaseModal[date]):

    def __init__(self, current_date: date) -> None:
        super().__init__()
        self.active_date = current_date
        self.selected_date = self.active_date

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static("Time Travel", id="modal-title")

            with Vertical(classes="form-content"):
                with Horizontal(classes="date-selector"):
                    yield Button("<", id="date-prev", classes="arrow-btn")
                    yield Label(
                        self.active_date.strftime("%m-%d-%Y"),
                        id="date-display",
                        classes="date-display",
                    )
                    yield Button(">", id="date-next", classes="arrow-btn")

            with Horizontal(classes="form-buttons"):
                yield Button("Confirm", id="confirm", variant="success")
                yield Button("Cancel", id="cancel", variant="error")

    @on(Button.Pressed)
    def handle_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "date-prev":
            if self.active_date < self.selected_date:
                self.selected_date -= timedelta(days=1)

                self.query_one("#date-display", Label).update(
                    self.selected_date.strftime("%m-%d-%Y")
                )
            else:
                self.notify("You cannot move backwards in time.", severity="error")

        elif event.button.id == "date-next":
            self.selected_date += timedelta(days=1)

            self.query_one("#date-display", Label).update(
                self.selected_date.strftime("%m-%d-%Y")
            )

        elif event.button.id == "confirm":
            self.active_date = self.selected_date

            if db.set_current_date(self.active_date):
                self.notify("Updating fines to movement in time.", severity="information")
                db.update_fines()
                self.dismiss(self.active_date)
            else:
                self.dismiss()

        elif event.button.id == "cancel":
            self.dismiss(None)
