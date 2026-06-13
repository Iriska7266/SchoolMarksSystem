"""Страница входа с запоминанием логина и пароля."""

import flet as ft
from database.connection import get_db
from services import authenticate_user
from session import save_credentials, load_credentials, clear_credentials


def login_page(page: ft.Page, on_login_success: callable):
    page.clean()
    page.title = "Школьная успеваемость — Вход"
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    saved = load_credentials()
    saved_login, saved_pass = (saved[0], saved[1]) if saved else ("", "")
    remember = saved is not None

    login_field = ft.TextField(
        label="Логин", width=300, value=saved_login,
        prefix_icon=ft.Icons.PERSON, border_radius=8, autofocus=True,
    )
    password_field = ft.TextField(
        label="Пароль", width=300, value=saved_pass,
        password=True, can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK, border_radius=8,
    )
    remember_cb = ft.Checkbox(label="Запомнить меня", value=remember)
    error_text = ft.Text("", color=ft.Colors.RED_700, size=13)

    def do_login(e):
        login = login_field.value.strip()
        password = password_field.value.strip()
        if not login or not password:
            error_text.value = "Введите логин и пароль"
            page.update()
            return
        db = get_db()
        try:
            account = authenticate_user(db, login, password)
            if account:
                if remember_cb.value:
                    save_credentials(login, password)
                else:
                    clear_credentials()
                page.data = {"user_id": account.user_id, "role": account.u_role, "login": account.login}
                on_login_success(page)
            else:
                error_text.value = "Неверный логин или пароль"
        except Exception as ex:
            clean = str(ex).replace('\ufffd', '?').encode('ascii', errors='replace').decode('ascii')
            error_text.value = f"Ошибка: {clean[:150]}"
        finally:
            db.close()
            page.update()

    def on_key(e: ft.KeyboardEvent):
        if e.key == "Enter":
            do_login(None)

    page.on_keyboard_event = on_key

    page.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.SCHOOL, size=56, color=ft.Colors.BLUE_800),
                    ft.Text("Школьная успеваемость", size=22, weight=ft.FontWeight.BOLD),
                    ft.Text("Вход в систему", size=14, color=ft.Colors.BLACK87),
                    ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                    login_field,
                    password_field,
                    remember_cb,
                    error_text,
                    ft.ElevatedButton(
                        "Войти", width=300,
                        on_click=do_login,
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_700,
                            shape=ft.RoundedRectangleBorder(radius=8),
                            padding=15,
                        ),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=30,
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            shadow=ft.BoxShadow(
                spread_radius=1, blur_radius=20,
                color=ft.Colors.BLACK26, offset=ft.Offset(0, 4),
            ),
        ),
    )
