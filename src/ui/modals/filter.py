from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Label, Button, Select, SelectionList, Static

from ui.custom import BaseModal

availability_options = ['All', 'Available', 'Unavailable']

class FilterModal(BaseModal):

    def __init__(self, filters: dict) -> None:
        super().__init__()

        self.filters = filters

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static("Filter", id="modal-title")

            with Vertical(classes="form-content"):
                with Horizontal(classes="filter-row"):
                    yield Label("Columns")
                    yield SelectionList[int](
                        *[(column[0], i, column[1]) for i, column in enumerate(self.filters['columns'])],
                        compact=True,
                        id="searched-columns"
                    )

                with Horizontal(classes="filter-row"):
                    yield Label("Availability")
                    yield Select.from_values(
                        availability_options,
                        allow_blank=False,
                        value=(self.filters['availability']),
                        id="availability-select",
                    )

            with Horizontal(classes="form-buttons"):
                yield Button("Confirm", id="confirm", variant="success")
                yield Button("Cancel", id="cancel", variant="error")

    def on_mount(self) -> None:
        self.query_one(SelectionList).border_title = "Searched Columns"

    @on(Button.Pressed)
    def handle_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.filter_availability()
            self.filter_columns()

            self.dismiss(self.filters)

        elif event.button.id == "cancel":
            self.dismiss(None)

    def filter_availability(self) -> None:
        self.filters['availability'] = str(self.query_one(Select).value)

    def filter_columns(self) -> None:
        selected_indices = self.query_one(SelectionList).selected
        filters = [(column[0], i in selected_indices) for i, column in enumerate(self.filters['columns'])]

        self.filters['columns'] = filters
