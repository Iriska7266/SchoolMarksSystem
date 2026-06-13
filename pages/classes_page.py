"""Страница классов — список → ученики → таблица оценок + расчёт итоговых."""

import flet as ft
from database.connection import get_db
from services import (
    get_classes, get_pupils_by_class, get_pupil_marks_grouped,
    recalc_performance_for_class,
)
from utils import format_date, format_gender
from components import page_header, primary_button, empty_state


def classes_page(page: ft.Page, on_navigate: callable):
    page.clean()
    page.title = "Классы"
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.scroll = ft.ScrollMode.AUTO

    db = get_db()
    try:
        classes = get_classes(db)
    except Exception as ex:
        page.add(ft.Column([ft.Text(f"Ошибка: {ex}", color=ft.Colors.RED)]))
        return
    finally:
        db.close()

    def show_pupils(class_id: int, class_title: str):
        page.controls.clear()
        page.title = "Класс"
        page.bgcolor = ft.Colors.BLUE_GREY_50

        page.add(ft.Text(f"Класс {class_title}: загрузка...", size=20, color=ft.Colors.BLUE))
        page.update()

        try:
            db2 = get_db()
            pupils = get_pupils_by_class(db2, class_id)
            db2.close()
        except Exception as ex:
            page.add(ft.Text(f"Ошибка БД: {ex}", color=ft.Colors.RED, size=20))
            page.update()
            return

        page.controls.clear()
        page.title = "Класс"
        page.bgcolor = ft.Colors.BLUE_GREY_50
        page.scroll = ft.ScrollMode.AUTO

        # Год набора
        class_year = next((c.get("form_year", "") for c in classes if c["class_id"] == class_id), "")

        lines = []
        for p in pupils:
            pid = p["pupil_id"]
            pname = p["full_name"]
            lines.append(
                ft.Container(
                    ft.Text(pname, size=16, weight=ft.FontWeight.W_500),
                    padding=14, bgcolor=ft.Colors.WHITE, border_radius=8,
                    on_click=lambda e, _pid=pid, _name=pname: show_marks(_pid, _name, class_id, class_title),
                )
            )

        page.add(ft.Column([
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: classes_page(page, on_navigate)),
                ft.Column([
                    ft.Text(f"{class_title}", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Год набора: {class_year}  |  {len(pupils)} уч.", size=13, color=ft.Colors.BLACK87),
                ]),
            ]),
            ft.Divider(),
            *([ft.Column(lines, spacing=8)] if lines else [ft.Text("Нет учеников")]),
        ], spacing=10))
        page.update()

    def _do_recalc(class_id: int, class_title: str):
        db3 = get_db()
        try:
            recalc_performance_for_class(db3, class_id)
        finally:
            db3.close()
        show_pupils(class_id, class_title)

    def show_marks(pupil_id: int, pupil_name: str, class_id: int, class_title: str):
        page.clean()
        page.title = "Оценки"
        page.bgcolor = ft.Colors.BLUE_GREY_50
        page.scroll = ft.ScrollMode.AUTO

        try:
            db2 = get_db()
            grouped = get_pupil_marks_grouped(db2, pupil_id)
            db2.close()
        except Exception as ex:
            page.add(ft.Column([ft.Text(f"Ошибка: {ex}", color=ft.Colors.RED, size=20)]))
            page.update()
            return

        all_dates = set()
        for g in grouped:
            for m in g["marks"]:
                all_dates.add(format_date(m["put_at"]))
        sorted_dates = sorted(all_dates)

        cols = [ft.DataColumn(ft.Text("Предмет", weight=ft.FontWeight.BOLD))]
        for d in sorted_dates[:15]:
            cols.append(ft.DataColumn(ft.Text(d, size=10)))

        tbl_rows = []
        for g in grouped:
            date_map = {format_date(m["put_at"]): m["mark_value"] for m in g["marks"]}
            cells = [ft.DataCell(ft.Text(g["subject"], weight=ft.FontWeight.W_500, size=13))]
            for d in sorted_dates[:15]:
                val = date_map.get(d)
                if val:
                    color = ft.Colors.GREEN if val >= 4 else (ft.Colors.AMBER if val == 3 else ft.Colors.RED)
                    cells.append(ft.DataCell(ft.Container(
                        ft.Text(str(val), color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=12),
                        bgcolor=color, padding=6, border_radius=4,
                    )))
                else:
                    cells.append(ft.DataCell(ft.Text("—", size=12, color=ft.Colors.GREY_400)))
            tbl_rows.append(ft.DataRow(cells=cells))

        page.add(
            ft.Column([
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: show_pupils(class_id, class_title)),
                    page_header(pupil_name, f"Журнал ({len(grouped)} предметов)"),
                ]),
                ft.Column([
                    ft.DataTable(columns=cols, rows=tbl_rows, column_spacing=8,
                                 border=ft.Border.all(1, ft.Colors.GREY_300),
                                 heading_row_height=40, data_row_max_height=40),
                ], scroll=ft.ScrollMode.AUTO) if tbl_rows else ft.Text("Нет оценок", size=16),
            ], spacing=10)
        )
        page.update()

    items = []
    for c in classes:
        cid = c["class_id"]
        ctitle = f'{c["c_number"]}{c["letter"]}'
        subtitle = f'Кл. рук.: {c["class_teacher_name"]}  |  {c["pupil_count"]} уч.'
        items.append(
            ft.Container(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.MEETING_ROOM, color=ft.Colors.ORANGE),
                    title=ft.Text(f'{c["c_number"]}{c["letter"]}', weight=ft.FontWeight.BOLD, size=18),
                    subtitle=ft.Text(subtitle),
                ),
                padding=8, bgcolor=ft.Colors.WHITE, border_radius=8, ink=True,
                on_click=lambda e, _cid=cid, _ctitle=ctitle: show_pupils(_cid, _ctitle),
            )
        )

    page.add(
        ft.Column([
            ft.Row([
                page_header("Классы", f"Всего: {len(classes)}"),
                ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: classes_page(page, on_navigate)),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Column(items, spacing=8),
        ], spacing=10)
    )
