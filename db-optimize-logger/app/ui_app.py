from nicegui import ui

from app.ui.pages import databases_page, main_page, queries_page

if __name__ in {"__main__", "__mp_main__"}:
    main_page()
    queries_page()
    databases_page()
    ui.run(
        host="0.0.0.0",
        port=8080,
        title="Build Queries and Datases",
        favicon="app/ui/static/favicon.ico",
    )
