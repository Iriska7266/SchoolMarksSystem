"""Переиспользуемые компоненты интерфейса Flet."""

import flet as ft
from typing import Callable


def themed_container(content: ft.Control, padding: int = 20) -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=10,
        bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=10,
            color=ft.Colors.BLACK12,
            offset=ft.Offset(0, 2),
        ),
    )


def card(title: str, value: str | int, icon: str, color: str = ft.Colors.BLUE) -> ft.Container:
    return themed_container(
        ft.Column(
            [
                ft.Icon(icon, color=color, size=32),
                ft.Text(value=str(value), size=28, weight=ft.FontWeight.BOLD),
                ft.Text(title, size=14, color=ft.Colors.BLACK87),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5,
        ),
        padding=15,
    )


def page_header(title: str, subtitle: str | None = None) -> ft.Column:
    return ft.Column(
        [
            ft.Text(title, size=28, weight=ft.FontWeight.BOLD),
            ft.Text(subtitle, size=14, color=ft.Colors.BLACK87) if subtitle else ft.Text(""),
        ],
        spacing=2,
    )


def create_text_field(label: str, value: str = "", multiline: bool = False,
                      password: bool = False, width: int = 300,
                      on_change: Callable | None = None) -> ft.TextField:
    return ft.TextField(
        label=label,
        value=value,
        multiline=multiline,
        password=password,
        can_reveal_password=password,
        width=width,
        border_radius=8,
        on_change=on_change,
    )


def create_dropdown(label: str, options: list[tuple[str, str]],
                    value: str | None = None, width: int = 300,
                    on_change: Callable | None = None) -> ft.Dropdown:
    return ft.Dropdown(
        label=label,
        options=[ft.dropdown.Option(key=k, text=v) for k, v in options],
        value=value,
        width=width,
        border_radius=8,
        on_select=on_change,
    )


def primary_button(text: str, on_click: Callable, icon: str | None = None) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        text,
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE_700,
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=(12, 20),
        ),
    )


def secondary_button(text: str, on_click: Callable, icon: str | None = None) -> ft.OutlinedButton:
    return ft.OutlinedButton(
        text,
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=(12, 20),
        ),
    )


def danger_button(text: str, on_click: Callable) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        text,
        on_click=on_click,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED_700,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
    )


def back_button(on_click: Callable) -> ft.IconButton:
    return ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        on_click=on_click,
        tooltip="Назад",
    )


def empty_state(message: str, icon: str = ft.Icons.INBOX) -> ft.Container:
    return ft.Container(
        ft.Column(
            [
                ft.Icon(icon, size=64, color=ft.Colors.GREY_700),
                ft.Text(message, size=16, color=ft.Colors.BLACK87),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        ),
        padding=50,
        alignment=ft.alignment.Alignment(0, 0),
    )


def error_snackbar(page: ft.Page, message: str):
    page.snack_bar = ft.SnackBar(
        content=ft.Text(message, color=ft.Colors.WHITE),
        bgcolor=ft.Colors.RED_700,
        duration=4000,
    )
    page.snack_bar.open = True
    page.update()


def success_snackbar(page: ft.Page, message: str):
    page.snack_bar = ft.SnackBar(
        content=ft.Text(message, color=ft.Colors.WHITE),
        bgcolor=ft.Colors.GREEN_700,
        duration=3000,
    )
    page.snack_bar.open = True
    page.update()


def create_table(columns: list[str], rows: list[list[str]],
                 on_row_click: Callable | None = None) -> ft.DataTable:
    return ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text(col, weight=ft.FontWeight.BOLD, size=14))
            for col in columns
        ],
        rows=[
            ft.DataRow(
                cells=[ft.DataCell(ft.Text(cell)) for cell in row],
                on_select_changed=lambda _, idx=i, data=row: on_row_click(idx, data) if on_row_click else None,
            )
            for i, row in enumerate(rows)
        ],
        border=ft.Border.all(1, ft.Colors.GREY_400),
        border_radius=8,
        vertical_lines=ft.BorderSide(1, ft.Colors.GREY_300),
        horizontal_lines=ft.BorderSide(1, ft.Colors.GREY_300),
        heading_row_height=50,
        data_row_max_height=45,
        column_spacing=30,
    )


def nav_drawer(page: ft.Page, user_role: str, current_route: str,
               on_navigate: Callable) -> ft.NavigationDrawer:
    items = get_nav_items(user_role, current_route)
    return ft.NavigationDrawer(
        items=items,
        bgcolor=ft.Colors.BLUE_GREY_50,
    )


def get_nav_items(role: str, current: str) -> list[ft.NavigationDrawerDestination]:
    all_items = [
        ("/dashboard", "Главная", ft.Icons.DASHBOARD),
        ("/pupils", "Ученики", ft.Icons.SCHOOL),
        ("/teachers", "Учителя", ft.Icons.PEOPLE),
        ("/classes", "Классы", ft.Icons.MEETING_ROOM),
        ("/subjects", "Предметы", ft.Icons.BOOK),
        ("/marks", "Оценки", ft.Icons.GRADE),
        ("/performance", "Успеваемость", ft.Icons.BAR_CHART),
        ("/parents", "Родители", ft.Icons.FAMILY_RESTROOM),
    ]

    items = []
    for route, label, icon in all_items:
        if role == "pupil" and route not in ("/dashboard", "/marks", "/performance"):
            continue
        if role == "parent" and route not in ("/dashboard", "/marks", "/performance", "/pupils"):
            continue
        items.append(
            ft.NavigationDrawerDestination(
                label=ft.Text(label, size=14),
                icon=icon,
                selected_icon=icon,
            )
        )
    return items


def app_bar(page: ft.Page, title: str, user_name: str,
            on_navigate: Callable, on_logout: Callable) -> ft.AppBar:
    return ft.AppBar(
        title=ft.Text(title),
        leading=ft.IconButton(ft.Icons.MENU, on_click=lambda e: page.open(nav_drawer(
            page, page.data.get("role", "") if page.data else "",
            "/", on_navigate
        ))),
        actions=[
            ft.Column(
                [ft.Text(user_name, size=14, weight=ft.FontWeight.W_500),
                 ft.Text("Выйти", size=11, color=ft.Colors.BLUE_200)],
                spacing=0,
                on_click=on_logout,
            ),
            ft.IconButton(ft.Icons.LOGOUT, on_click=on_logout),
        ],
        bgcolor=ft.Colors.BLUE_800,
        color=ft.Colors.WHITE,
    )
