"""Страница учителей — список + предметы."""

import flet as ft
from database.connection import get_db
from services import get_teachers, get_teacher_subjects, get_teacher_classes
from utils import format_date, format_gender
from components import page_header, empty_state


def teachers_page(page: ft.Page, on_navigate: callable):
    page.clean()
    page.title = "Учителя"
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.scroll = ft.ScrollMode.AUTO

    db = get_db()
    try:
        teachers = get_teachers(db)
    except Exception as ex:
        page.add(ft.Column([ft.Text(f"Ошибка: {ex}")]))
        return
    finally:
        db.close()

    def refresh():
        teachers_page(page, on_navigate)

    def show_details(teacher_id: int, teacher_name: str):
        page.clean()
        page.title = "Учитель"
        page.bgcolor = ft.Colors.BLUE_GREY_50
        page.scroll = ft.ScrollMode.AUTO
        db2 = get_db()
        try:
            subjects = get_teacher_subjects(db2, teacher_id)
            classes = get_teacher_classes(db2, teacher_id)
        finally:
            db2.close()
        subj = [ft.Container(ft.Text(s.title, size=15), padding=10, bgcolor=ft.Colors.WHITE, border_radius=8) for s in subjects]
        cls = [ft.Container(ft.Text(c["title"], size=15), padding=10, bgcolor=ft.Colors.WHITE, border_radius=8) for c in classes]
        page.add(ft.Column([
            ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: refresh()),
                    page_header(teacher_name, "Предметы и классы")]),
            ft.Text("Предметы", size=16, weight=ft.FontWeight.BOLD),
            ft.Column(subj, spacing=6) if subj else empty_state("Нет"),
            ft.Divider(),
            ft.Text("Классы", size=16, weight=ft.FontWeight.BOLD),
            ft.Column(cls, spacing=6) if cls else empty_state("Нет"),
        ], spacing=10))

    items = []
    for t in teachers:
        role = "Завуч" if t["head_teacher"] else "Учитель"
        items.append(ft.Container(
            ft.Text(f"{t['full_name']}  ({role})", size=16),
            padding=14, bgcolor=ft.Colors.WHITE, border_radius=8, ink=True,
            on_click=lambda _, tid=t["teacher_id"], name=t["full_name"]: show_details(tid, name),
        ))

    page.add(ft.Column([
        ft.Row([page_header("Учителя", f"Всего: {len(teachers)}"),
                ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: refresh())],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        ft.Column(items, spacing=8),
    ], spacing=10))
