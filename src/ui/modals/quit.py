from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Static

from ui.custom import BaseModal

class QuitModal(BaseModal[bool]):

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static("Are you sure you want to quit?", id="modal-title")

            with Horizontal(classes="form-buttons"):
                yield Button("Quit", variant="error", id="quit-btn")
                yield Button("Cancel", variant="primary", id="cancel-btn")

    @on(Button.Pressed)
    def handle_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit-btn":
            self.app.exit()
            self.dismiss(True)
        else:
            self.app.pop_screen()
            self.dismiss(False)
