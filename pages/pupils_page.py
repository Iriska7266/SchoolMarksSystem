"""Страница учеников — список + журнал оценок."""

import flet as ft
from database.connection import get_db
from services import get_pupils, get_pupil_marks_grouped
from utils import format_date, format_gender
from components import page_header, empty_state


def pupils_page(page: ft.Page, on_navigate: callable):
    page.clean()
    page.title = "Ученики"
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.scroll = ft.ScrollMode.AUTO

    db = get_db()
    try:
        pupils = get_pupils(db)
    except Exception as ex:
        page.add(ft.Column([ft.Text(f"Ошибка: {ex}")]))
        return
    finally:
        db.close()

    def refresh():
        pupils_page(page, on_navigate)

    def show_marks(pupil_id: int, pupil_name: str):
        page.clean()
        page.title = "Оценки"
        page.bgcolor = ft.Colors.BLUE_GREY_50
        page.scroll = ft.ScrollMode.AUTO
        try:
            db2 = get_db()
            grouped = get_pupil_marks_grouped(db2, pupil_id)
            db2.close()
        except Exception as ex:
            page.add(ft.Column([ft.Text(f"Ошибка: {ex}", color=ft.Colors.RED)]))
            return
        from collections import defaultdict
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
                    cells.append(ft.DataCell(ft.Container(ft.Text(str(val), color=ft.Colors.WHITE,
                        weight=ft.FontWeight.BOLD, size=12), bgcolor=color, padding=6, border_radius=4)))
                else:
                    cells.append(ft.DataCell(ft.Text("—", size=12, color=ft.Colors.GREY_400)))
            tbl_rows.append(ft.DataRow(cells=cells))
        page.add(ft.Column([
            ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: refresh()),
                    page_header(pupil_name, f"Журнал ({len(grouped)})")]),
            ft.TextButton("Сформировать отчёт", icon=ft.Icons.CALCULATE,
                on_click=lambda _: _gen_report(pupil_id, pupil_name)),
            ft.Column([ft.DataTable(columns=cols, rows=tbl_rows, column_spacing=8,
                border=ft.Border.all(1, ft.Colors.GREY_300), heading_row_height=40, data_row_max_height=40)],
                scroll=ft.ScrollMode.AUTO) if tbl_rows else ft.Text("Нет оценок"),
        ], spacing=10))

    def _gen_report(pupil_id, pupil_name):
        page.add(ft.Text("Генерация...", color=ft.Colors.BLUE))
        page.update()
        from services import recalc_performance_for_pupil, get_performance
        db = get_db()
        try:
            cnt = recalc_performance_for_pupil(db, pupil_id)
        except Exception as ex:
            page.controls.pop()
            page.add(ft.Text(f"✗ Ошибка: {ex}", color=ft.Colors.RED, size=16, selectable=True))
            page.update()
            db.close()
            return

        # Загружаем итоговые оценки
        try:
            perf = get_performance(db, pupil_id=pupil_id)
        except Exception as ex:
            page.controls.pop()
            page.add(ft.Text(f"✗ Ошибка загрузки отчёта: {ex}", color=ft.Colors.RED, size=16))
            page.update()
            db.close()
            return
        finally:
            db.close()

        page.controls.pop()  # убираем "Генерация..."
        # Добавляем блок с итоговыми оценками
        perf_lines = [ft.Text("Итоговые оценки:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)]
        for p in perf:
            perf_lines.append(ft.Container(
                ft.Text(f"{p['subject_title']}: {p['final_mark']}  (баллы: {p['mark_total']}, вес: {p['weights_sum']})",
                        size=14),
                padding=6, bgcolor=ft.Colors.GREEN_50, border_radius=6,
            ))
        avg = sum(p["final_mark"] for p in perf) / len(perf) if perf else 0
        perf_lines.append(ft.Text(f"Средний балл: {avg:.2f}", size=15, weight=ft.FontWeight.BOLD))
        page.add(ft.Column(perf_lines, spacing=4))
        page.update()

    items = []
    for p in pupils:
        items.append(ft.Container(
            ft.Text(f"{p['full_name']}  ({format_gender(p['gender'])})", size=16),
            padding=14, bgcolor=ft.Colors.WHITE, border_radius=8, ink=True,
            on_click=lambda _, pid=p["pupil_id"], name=p["full_name"]: show_marks(pid, name),
        ))

    page.add(ft.Column([
        ft.Row([page_header("Ученики", f"Всего: {len(pupils)}"),
                ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: refresh())],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        ft.Column(items, spacing=8),
    ], spacing=10))
