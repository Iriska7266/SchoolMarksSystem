"""Страница успеваемости — сводный отчёт с фильтром по роли."""

import flet as ft
from database.connection import get_db
from services import get_performance, get_classes, get_own_pupil_id, get_parent_children_ids
from components import page_header, create_dropdown, empty_state


def performance_page(page: ft.Page, on_navigate: callable):
    page.clean()
    page.title = "Успеваемость"
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.scroll = ft.ScrollMode.AUTO

    role = (page.data or {}).get("role", "")
    user_id = (page.data or {}).get("user_id", 0)

    db = get_db()
    try:
        classes = get_classes(db)
        # Фильтр данных по роли
        if role == "pupil":
            pid = get_own_pupil_id(db, user_id)
            all_data = get_performance(db, pupil_id=pid) if pid else []
        elif role == "parent":
            children = get_parent_children_ids(db, user_id)
            all_data = []
            for cid in children:
                all_data.extend(get_performance(db, pupil_id=cid))
        else:
            all_data = get_performance(db)
    except Exception as ex:
        page.add(ft.Column([ft.Text(f"Ошибка: {ex}")]))
        return
    finally:
        db.close()

    class_opts = [("", "Все классы")] + [(str(c["class_id"]), f'{c["c_number"]}{c["letter"]}') for c in classes]

    def show_report(class_id=None):
        page.clean()
        page.title = "Успеваемость"
        page.bgcolor = ft.Colors.BLUE_GREY_50
        page.scroll = ft.ScrollMode.AUTO

        db2 = get_db()
        try:
            if role == "pupil":
                pid = get_own_pupil_id(db2, user_id)
                data = get_performance(db2, pupil_id=pid, class_id=class_id) if pid else []
            elif role == "parent":
                children = get_parent_children_ids(db2, user_id)
                data = []
                for cid in children:
                    data.extend(get_performance(db2, pupil_id=cid, class_id=class_id))
            else:
                data = get_performance(db2, class_id=class_id)
        finally:
            db2.close()

        dd = create_dropdown("Фильтр", class_opts, str(class_id) if class_id else "",
                              width=250, on_change=lambda e: show_report(int(e.control.value) if e.control.value else None))

        parts = [ft.Row([page_header("Успеваемость", "Сводный отчёт"), dd])]

        if not data:
            parts.append(empty_state("Нет данных"))
        else:
            from collections import defaultdict
            by_pupil = defaultdict(list)
            for r in data:
                by_pupil[r["pupil_name"]].append(r)

            avg_all = sum(r["final_mark"] for r in data) / len(data)
            parts.append(
                ft.Container(
                    ft.Row([
                        ft.Text("Средний балл: ", size=16),
                        ft.Container(
                            ft.Text(f"{avg_all:.2f}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.BLUE_700, padding=12, border_radius=8,
                        ),
                    ]),
                    padding=12, bgcolor=ft.Colors.WHITE, border_radius=8,
                )
            )

            for pupil_name, records in by_pupil.items():
                avg_p = sum(r["final_mark"] for r in records) / len(records)
                marks_text = "  ".join([str(r["final_mark"]) for r in records])
                subjects_text = " | ".join([f"{r['subject_title']}: {r['final_mark']}" for r in records])
                parts.append(
                    ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(pupil_name, weight=ft.FontWeight.BOLD, expand=True),
                                ft.Text(f"Ср.: {avg_p:.2f}", size=13),
                            ]),
                            ft.Text(f"Оценки: {marks_text}", size=13),
                            ft.Text(subjects_text, size=11, color=ft.Colors.BLACK87),
                        ], spacing=4),
                        padding=10, bgcolor=ft.Colors.WHITE, border_radius=8,
                    )
                )

        page.add(ft.Column(parts, spacing=10))
        page.update()

    show_report()
