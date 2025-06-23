from nicegui import ui

from app.ui.pages import databases_page, main_page, queries_page

if __name__ in {"__main__", "__mp_main__"}:
    main_page()
    queries_page()
    databases_page()
    ui.run(title="Build Queries and Datases")
