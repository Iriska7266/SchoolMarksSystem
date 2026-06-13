"""Точка входа приложения — система управления школьной успеваемостью."""

import flet as ft
from database.connection import db_manager, get_db
from pages.login_page import login_page
from pages.dashboard_page import dashboard_page
from pages.pupils_page import pupils_page
from pages.teachers_page import teachers_page
from pages.classes_page import classes_page
from pages.subjects_page import subjects_page
from pages.marks_page import marks_page
from pages.performance_page import performance_page
from pages.parents_page import parents_page


def on_login_success(page: ft.Page):
    """Обработчик успешного входа — переходит на дашборд."""
    navigate_to(page, "/dashboard")


def _build_nav(page: ft.Page, sel: int):
    """Создаёт BottomAppBar с фильтрацией по роли пользователя."""
    role = (page.data or {}).get("role", "")
    all_items = [
        (0, "/dashboard", "Главная", ft.Icons.DASHBOARD),
        (1, "/pupils", "Ученики", ft.Icons.SCHOOL),
        (2, "/teachers", "Учителя", ft.Icons.PEOPLE),
        (3, "/classes", "Классы", ft.Icons.MEETING_ROOM),
        (4, "/subjects", "Предметы", ft.Icons.BOOK),
        (5, "/marks", "Оценки", ft.Icons.GRADE),
        (6, "/performance", "Успеваемость", ft.Icons.BAR_CHART),
        (7, "/parents", "Родители", ft.Icons.FAMILY_RESTROOM),
    ]

    # Фильтр по ролям
    role_visibility = {
        "headteacher": [0, 1, 2, 3, 4, 5, 6, 7],
        "teacher":     [0, 1, 3, 4, 5, 6, 7],
        "pupil":       [0, 5, 6],
        "parent":      [0, 5, 6],
    }
    visible = role_visibility.get(role, [0, 5, 6])

    visible_items = [(i, r, l, ic) for i, r, l, ic in all_items if i in visible]
    routes = [r for _, r, _, _ in visible_items]
    page.data["_routes"] = routes

    # Находим новый selected_index
    try:
        new_sel = routes.index(
            [r for _, r, _, _ in visible_items][min(sel, len(visible_items) - 1)]
        ) if visible_items else 0
    except (ValueError, IndexError):
        new_sel = 0

    btns = []
    for idx_in_bar, (_, route, label, icon) in enumerate(visible_items):
        color = ft.Colors.WHITE if idx_in_bar == new_sel else ft.Colors.WHITE70
        btns.append(
            ft.Container(
                content=ft.Column([
                    ft.Icon(icon, color=color, size=20),
                    ft.Text(label, size=9, color=color, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1),
                expand=True,
                on_click=lambda _, r=route: navigate_to(page, r),
            )
        )

    page.bottom_appbar = ft.BottomAppBar(
        content=ft.Row(btns, spacing=0),
        bgcolor=ft.Colors.BLUE_900,
        padding=0,
    )


def navigate_to(page: ft.Page, route: str):
    """Навигация по страницам приложения."""
    # Сначала строим навбар (он обновляет page.data["_routes"] с учётом роли)
    _build_nav(page, 0)

    routes = page.data.get("_routes", [])
    try:
        idx = routes.index(route)
    except ValueError:
        idx = 0

    # Сохраняем _build_nav для доступа из страниц
    page.data["_build_nav"] = _build_nav

    handlers = {
        "/dashboard": lambda: dashboard_page(page, navigate_to),
        "/pupils": lambda: pupils_page(page, navigate_to),
        "/teachers": lambda: teachers_page(page, navigate_to),
        "/classes": lambda: classes_page(page, navigate_to),
        "/subjects": lambda: subjects_page(page, navigate_to),
        "/marks": lambda: marks_page(page, navigate_to),
        "/performance": lambda: performance_page(page, navigate_to),
        "/parents": lambda: parents_page(page, navigate_to),
    }

    handler = handlers.get(route)
    if handler:
        try:
            _build_nav(page, idx)
            handler()
        except Exception as ex:
            page.clean()
            _build_nav(page, idx)
            page.add(
                ft.Container(
                    ft.Column([
                        ft.Icon(ft.Icons.ERROR, size=64, color=ft.Colors.RED_700),
                        ft.Text("Ошибка загрузки страницы", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_900),
                        ft.Text(str(ex), size=14, color=ft.Colors.RED_800, selectable=True),
                        ft.ElevatedButton("На главную", on_click=lambda _: navigate_to(page, "/dashboard")),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16),
                    alignment=ft.alignment.Alignment(0, 0),
                    expand=True,
                )
            )
    else:
        _build_nav(page, idx)
        dashboard_page(page, navigate_to)

    page.update()


def _nav_changed(page: ft.Page, e):
    """Обработчик смены вкладки в нижней навигации."""
    routes = page.data.get("_routes", [])
    idx = e.control.selected_index
    if 0 <= idx < len(routes):
        navigate_to(page, routes[idx])


def main(page: ft.Page):
    """Главная функция запуска приложения."""
    page.title = "Школьная успеваемость"
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.BLUE_800,
            secondary=ft.Colors.TEAL_700,
        ),
        font_family="Segoe UI",
    )
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.data = {}

    # Попытка подключиться к БД
    try:
        db_manager.connect()
        # Проверяем соединение реальным запросом
        db = get_db()
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        err_msg = str(e)
        auth_help = ""
        if "28P01" in err_msg or "auth_failed" in err_msg or "password" in err_msg.lower():
            auth_help = (
                "\n\n💡 Убедитесь, что в .env указан правильный пароль "
                "от пользователя postgres (тот, что вы задали при установке PostgreSQL)."
            )
        page.add(
            ft.Container(
                ft.Column([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color=ft.Colors.RED_700),
                    ft.Text("Не удалось подключиться к базе данных", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Ошибка: {err_msg[:200]}", size=13, color=ft.Colors.RED_800),
                    ft.Text(
                        "Настройте переменные окружения в файле .env:\n"
                        "DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD"
                        + auth_help,
                        size=13, color=ft.Colors.BLACK87,
                    ),
                    ft.ElevatedButton("Повторить попытку", on_click=lambda _: main(page)),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                padding=40,
                alignment=ft.alignment.Alignment(0, 0),
            )
        )
        return

    # Показываем страницу входа
    login_page(page, on_login_success)


if __name__ == "__main__":
    ft.app(target=main)
