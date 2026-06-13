"""Страница родителей — список + дети."""

import flet as ft
from database.connection import get_db
from services import get_parents, get_parent_children, get_teacher_class_parents
from utils import format_date, format_gender
from components import page_header, empty_state

RELATION_RU = {"mother": "Мать", "father": "Отец", "guardian": "Опекун",
               "grandmother": "Бабушка", "grandfather": "Дедушка"}


def parents_page(page: ft.Page, on_navigate: callable):
    page.clean()
    page.title = "Родители"
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.scroll = ft.ScrollMode.AUTO

    role = (page.data or {}).get("role", "")
    user_id = (page.data or {}).get("user_id", 0)

    db = get_db()
    try:
        if role == "teacher":
            parents = get_teacher_class_parents(db, user_id)
        else:
            parents = get_parents(db)
    except Exception as ex:
        page.add(ft.Column([ft.Text(f"Ошибка: {ex}")]))
        return
    finally:
        db.close()

    def refresh():
        parents_page(page, on_navigate)

    def show_children(parent_id: int, parent_name: str):
        page.clean()
        page.title = "Дети"
        page.bgcolor = ft.Colors.BLUE_GREY_50
        page.scroll = ft.ScrollMode.AUTO
        db2 = get_db()
        try:
            children = get_parent_children(db2, parent_id)
        finally:
            db2.close()
        items = [ft.Container(ft.Text(f"{c['full_name']}  ({RELATION_RU.get(c['relation'], c['relation'])})",
            size=15), padding=10, bgcolor=ft.Colors.WHITE, border_radius=8) for c in children]
        page.add(ft.Column([
            ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: refresh()),
                    page_header(parent_name, "Дети")]),
            ft.Column(items, spacing=6),
        ], spacing=10))

    items = []
    for p in parents:
        if "children" in p and p["children"]:
            subtitle = "  |  ".join(f'{c["full_name"]}' for c in p["children"])
        else:
            subtitle = f'{format_gender(p["gender"])}  |  {p.get("login", "")}'
        items.append(ft.Container(
            ft.Column([
                ft.Text(p["full_name"], size=16, weight=ft.FontWeight.W_500),
                ft.Text(subtitle, size=12, color=ft.Colors.BLACK87),
            ]),
            padding=14, bgcolor=ft.Colors.WHITE, border_radius=8, ink=True,
            on_click=lambda _, pid=p["parent_id"], name=p["full_name"]: show_children(pid, name),
        ))

    page.add(ft.Column([
        ft.Row([page_header("Родители", f"Всего: {len(parents)}"),
                ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: refresh())],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        ft.Column(items, spacing=8),
    ], spacing=10))
