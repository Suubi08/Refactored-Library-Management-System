from datetime import date
from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button
from textual.containers import Container, Grid

from ui.components.navbar import NavbarComponent
from ui.modals import QuitModal, TimeTravelModal, CreateBorrowerModal, SettingsModal, InitModal
from ui.screens import BookSearchScreen, BorrowerSearchScreen

import database as db

class HomeScreen(Screen):
    SUB_TITLE = "Home"

    def __init__(self, current_date: Optional[date] = None) -> None:
        super().__init__()
        self.current_date = current_date or date.today()

    def compose(self) -> ComposeResult:
        yield NavbarComponent(
            left_button=Button("Quit", id="quit-btn", variant="error"),
            right_button=Button(self.current_date.strftime("%m-%d-%Y"), id="time-travel-btn")
        )

        with Container(classes="content"):
            with Grid(classes="menu-grid"):
                yield Button("Search Books", id="search-books", classes="menu-btn", variant="primary", disabled=(not db.is_initialized()))
                yield Button("Search Borrowers", id="search-borrowers", classes="menu-btn", variant="primary", disabled=(not db.is_initialized()))
                yield Button("Create A Borrower", id="create-borrower", classes="menu-btn", variant="primary", disabled=(not db.is_initialized()))
                yield Button("Settings", id="settings", classes="menu-btn", variant="primary")

        # Footer (empty for now)
        yield Container(classes="footer")

    def on_mount(self) -> None:
        if not db.is_initialized():
            self.app.push_screen(InitModal())

    def on_screen_resume(self) -> None:
        self.refresh_data()

    def refresh_data(self) -> None:
        self.current_date = db.get_current_date() or date.today()

        nav = self.query_one(NavbarComponent)
        ttb = nav.query_one('#time-travel-btn', Button)
        ttb.label = self.current_date.strftime("%m-%d-%Y")

        menubtns = self.query(".menu-btn")
        for btn in menubtns:
            if btn.id == "settings":
                continue
            btn.disabled = not db.is_initialized()

    @on(Button.Pressed)
    def handle_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit-btn":
            self.app.push_screen(QuitModal(), self.handle_quit)
        elif event.button.id == "time-travel-btn":
            self.app.push_screen(
                TimeTravelModal(self.current_date),
                self.handle_time_travel,
            )
        elif event.button.id == "search-books":
            self.app.push_screen(BookSearchScreen())
        elif event.button.id == "search-borrowers":
            self.app.push_screen(BorrowerSearchScreen())
        elif event.button.id == "create-borrower":
            self.app.push_screen(CreateBorrowerModal())
        elif event.button.id == "settings":
            self.app.push_screen(SettingsModal())

    def handle_quit(self, should_quit: bool) -> None:
        if should_quit:
            self.app.exit()

    def handle_time_travel(self, new_date: Optional[date]) -> None:
        if new_date:
            self.current_date = new_date
            self.query_one("#time-travel-btn", Button).label = new_date.strftime("%m-%d-%Y")
