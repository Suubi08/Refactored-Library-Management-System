from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Static, Header

class NavbarComponent(Static):

    def __init__(
        self,
        left_button: Button | None = None,
        title: str = "",
        right_button: Button | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.left_button = left_button
        self.title_text = title
        self.right_button = right_button

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal():
            with Container(classes="nav-left"):
                if self.left_button:
                    yield self.left_button
                else:
                    yield Static("", classes="nav-placeholder")

            with Container(classes="nav-center"):
                yield Static(self.title_text, classes="nav-title")

            with Container(classes="nav-right"):
                if self.right_button:
                    yield self.right_button
                else:
                    yield Static("", classes="nav-placeholder")
