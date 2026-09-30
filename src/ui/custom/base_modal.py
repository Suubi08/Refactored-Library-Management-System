from typing import TypeVar, Generic

from textual.screen import ModalScreen
from textual.binding import Binding

T = TypeVar('T')

class BaseModal(ModalScreen[T], Generic[T]):
    BINDINGS = [
        Binding("escape", "dismiss", "Cancel", show=False),
    ]

    def action_dismiss(self) -> None:
        self.dismiss(None)
