from datetime import date
from textual.app import App

from ui.screens import HomeScreen

import database as db

class LibraryApp(App):
    TITLE = "Library Management System"
    SUB_TITLE = ""

    CSS_PATH = [
        "ui/styles/global/modal.tcss",
        "ui/styles/global/form.tcss",

        "ui/styles/home-screen.tcss",
        "ui/styles/search-screen.tcss",

        "ui/styles/time-travel-modal.tcss",
        "ui/styles/filter-modal.tcss",

        "ui/styles/navbar-component.tcss",
        "ui/styles/tag-component.tcss",
    ]

    def on_mount(self) -> None:
        if not db.config.db_name:
            db.config.set_db_name("library.db")

        today = None
        if db.exists(db.config.db_name) and db.is_initialized():
            today = db.get_current_date()
            db.update_fines()

        self.push_screen(HomeScreen(today or date.today()))

app = LibraryApp()

if __name__ == '__main__':
    app.run()
