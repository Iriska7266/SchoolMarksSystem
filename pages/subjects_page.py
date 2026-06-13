"""Страница предметов — список + преподаватели."""

import flet as ft
from database.connection import get_db
from services import get_subjects, get_subject_teachers
from components import page_header, empty_state


def subjects_page(page: ft.Page, on_navigate: callable):
    page.clean()
    page.title = "Предметы"
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.scroll = ft.ScrollMode.AUTO

    db = get_db()
    try:
        subjects = get_subjects(db)
    except Exception as ex:
        page.add(ft.Column([ft.Text(f"Ошибка: {ex}")]))
        return
    finally:
        db.close()

    def show_teachers(subject_id: int, subject_title: str):
        page.clean()
        page.title = "Преподаватели"
        page.bgcolor = ft.Colors.BLUE_GREY_50
        page.scroll = ft.ScrollMode.AUTO
        db2 = get_db()
        try:
            teachers = get_subject_teachers(db2, subject_id)
        finally:
            db2.close()
        items = [ft.Container(ft.Text(t["full_name"], size=15), padding=10,
                 bgcolor=ft.Colors.WHITE, border_radius=8) for t in teachers]
        page.add(ft.Column([
            ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: subjects_page(page, on_navigate)),
                    page_header(subject_title, "Преподаватели")]),
            ft.Column(items, spacing=6),
        ], spacing=10))

    items = []
    for s in subjects:
        items.append(ft.Container(
            ft.Text(s.title, size=16, weight=ft.FontWeight.W_500),
            padding=14, bgcolor=ft.Colors.WHITE, border_radius=8, ink=True,
            on_click=lambda _, sid=s.subject_id, title=s.title: show_teachers(sid, title),
        ))

    page.add(ft.Column([
        ft.Row([page_header("Предметы", f"Всего: {len(subjects)}"),
                ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: subjects_page(page, on_navigate))],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        ft.Column(items, spacing=8),
    ], spacing=10))
