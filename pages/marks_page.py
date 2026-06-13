"""Страница оценок — фильтр по роли и классу."""

import flet as ft
from database.connection import get_db
from services import get_marks, get_classes, get_own_pupil_id, get_parent_children_ids
from components import page_header, create_dropdown, empty_state


def marks_page(page: ft.Page, on_navigate: callable):
    page.clean()
    page.title = "Оценки"
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.scroll = ft.ScrollMode.AUTO

    role = (page.data or {}).get("role", "")
    user_id = (page.data or {}).get("user_id", 0)

    db = get_db()
    try:
        classes = get_classes(db)
        if role == "pupil":
            pid = get_own_pupil_id(db, user_id)
            marks = get_marks(db, pupil_id=pid) if pid else []
        elif role == "parent":
            children = get_parent_children_ids(db, user_id)
            marks = []
            for cid in children:
                marks.extend(get_marks(db, pupil_id=cid))
        else:
            marks = get_marks(db)
    except Exception as ex:
        page.add(ft.Column([ft.Text(f"Ошибка: {ex}")]))
        page.update()
        return
    finally:
        db.close()

    class_opts = [("", "Все классы")] + [(str(c["class_id"]), f'{c["c_number"]}{c["letter"]}') for c in classes]

    def _filter(class_id=None):
        db2 = get_db()
        try:
            if role == "pupil":
                pid = get_own_pupil_id(db2, user_id)
                data = get_marks(db2, pupil_id=pid, class_id=class_id) if pid else []
            elif role == "parent":
                children = get_parent_children_ids(db2, user_id)
                data = []
                for cid in children:
                    data.extend(get_marks(db2, pupil_id=cid, class_id=class_id))
            else:
                data = get_marks(db2, class_id=class_id)
        finally:
            db2.close()
        _build_view(data)

    def _build_view(marks_list):
        page.controls.clear()
        page.title = "Оценки"
        page.bgcolor = ft.Colors.BLUE_GREY_50
        page.scroll = ft.ScrollMode.AUTO

        dd = create_dropdown("Фильтр по классу", class_opts, "", width=300,
                              on_change=lambda e: _filter(int(e.control.value) if e.control.value else None))
        header = ft.Row([page_header("Оценки", f"Всего: {len(marks_list)}"), dd])

        if not marks_list:
            page.add(header, ft.Text("Нет оценок", size=16))
            page.update()
            return

        from collections import defaultdict
        grouped = defaultdict(list)
        for m in marks_list:
            grouped[m["pupil_name"]].append(m)

        sections = []
        for pupil_name, pupil_marks in grouped.items():
            chips_text = "  ".join(str(m["mark_value"]) for m in pupil_marks)
            sections.append(
                ft.Container(
                    ft.Column([
                        ft.Text(pupil_name, weight=ft.FontWeight.BOLD),
                        ft.Text(chips_text, size=16),
                    ], spacing=4),
                    padding=8, bgcolor=ft.Colors.WHITE, border_radius=8,
                )
            )

        page.add(header, ft.Divider(), ft.Column(sections, spacing=6))
        page.update()

    _build_view(marks)
