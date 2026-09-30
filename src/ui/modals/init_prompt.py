from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Static

from ui.custom import BaseModal

from database import config
import database as db

class InitModal(BaseModal):

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static("You need to initialize the database on first run.", id="modal-title")

            with Horizontal(classes="form-buttons"):
                yield Button("Init Database", variant="primary", id="cancel-btn")
                yield Button("Quit App", variant="error", id="quit-btn")

    @on(Button.Pressed)
    def handle_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit-btn":
            self.app.exit()
            self.dismiss()
        else:
            db_exists = db.exists(config.db_name)

            if not db_exists:
                success = db.init(config.db_name)

                if success:
                    self.notify("Database initialized successfully!", severity="information")
                    self.dismiss()
                else:
                    self.notify("Database failed to initialize!", severity="error")

            else:
                self.notify(f"Database already exists at {config.db_name}!", severity="error")

            self.dismiss()
