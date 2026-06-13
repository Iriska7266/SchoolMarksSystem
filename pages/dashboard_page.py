"""Главная страница — дашборд со статистикой."""

import flet as ft
from database.connection import get_db
from services import get_dashboard_stats
from components import page_header, card, themed_container, empty_state


def dashboard_page(page: ft.Page, on_navigate=None):
    page.clean()
    page.title = "Школьная успеваемость — Главная"
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.scroll = ft.ScrollMode.AUTO

    db = get_db()
    try:
        stats = get_dashboard_stats(db)
    except Exception as ex:
        page.add(ft.Text(f"Ошибка загрузки: {ex}", color=ft.Colors.RED))
        return
    finally:
        db.close()

    routes = ["/dashboard", "/pupils", "/teachers", "/classes",
              "/subjects", "/marks", "/performance", "/parents"]

    class_cards = []
    for cls in stats["classes"]:
        class_cards.append(
            themed_container(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.GROUP, color=ft.Colors.BLUE),
                    title=ft.Text(f'{cls["c_number"]}{cls["letter"]}', weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(f'Кл. рук.: {cls["class_teacher_name"]}  |  Учеников: {cls["pupil_count"]}'),
                ),
                padding=10,
            )
        )

    page.add(
        ft.Column([
            page_header("Панель управления", "Общая статистика системы"),
            ft.Divider(height=10),
            ft.ResponsiveRow(
                [
                    ft.Column([card("Учеников", stats["total_pupils"], ft.Icons.SCHOOL, ft.Colors.BLUE)], col={"sm": 6, "md": 3}),
                    ft.Column([card("Учителей", stats["total_teachers"], ft.Icons.PEOPLE, ft.Colors.GREEN)], col={"sm": 6, "md": 3}),
                    ft.Column([card("Классов", stats["total_classes"], ft.Icons.MEETING_ROOM, ft.Colors.ORANGE)], col={"sm": 6, "md": 3}),
                    ft.Column([card("Предметов", stats["total_subjects"], ft.Icons.BOOK, ft.Colors.PURPLE)], col={"sm": 6, "md": 3}),
                    ft.Column([card("Оценок", stats["total_marks"], ft.Icons.GRADE, ft.Colors.AMBER)], col={"sm": 6, "md": 3}),
                    ft.Column([card("Родителей", stats["total_parents"], ft.Icons.FAMILY_RESTROOM, ft.Colors.TEAL)], col={"sm": 6, "md": 3}),
                    ft.Column([card("Средний балл", stats["avg_mark"], ft.Icons.TRENDING_UP, ft.Colors.RED)], col={"sm": 6, "md": 3}),
                    ft.Column([card("Школ", stats["total_schools"], ft.Icons.LOCATION_CITY, ft.Colors.INDIGO)], col={"sm": 6, "md": 3}),
                ],
                spacing=10, run_spacing=10,
            ),
            ft.Divider(height=20),
            ft.Text("Классы", size=20, weight=ft.FontWeight.BOLD),
            ft.Column(class_cards, spacing=10) if class_cards else empty_state("Нет классов"),
        ], spacing=15, scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
    page.update()
