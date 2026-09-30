from textual.widgets import Static
from textual.message import Message

class Tag(Static):
    class Clicked(Message):
        def __init__(self, title: str) -> None:
            self.title = title
            super().__init__()

    def __init__(self, title: str) -> None:
        super().__init__(title)
        self.title = title

    def on_click(self) -> None:
        self.post_message(self.Clicked(self.title))
