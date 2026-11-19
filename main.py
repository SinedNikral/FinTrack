import sys

from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QStackedWidget,
    QWidget,
    QLabel
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice
from PySide6.QtGui import QPixmap, QKeySequence, QShortcut
from database.db import init_database
from pages.categories_page import CategoriesPageController
from pages.transactions_page import TransactionsPageController
from pages.dashboard_page import DashboardPageController
from pages.budget_page import BudgetPageController
from pages.analytics_page import AnalyticsPageController
from pages.reports_page import ReportsPageController
from pathlib import Path

# Определяем папку с ресурсами приложения
BASE_DIR = Path(
    getattr(
        sys,
        "_MEIPASS",
        Path(__file__).resolve().parent
    )
)

def main():
    app = QApplication(sys.argv)

    init_database()

    # Создаём загрузчик интерфейса
    loader = QUiLoader()

    # Открываем файл Qt Designer
    ui_path = BASE_DIR / "ui" / "main_window.ui"
    ui_file = QFile(str(ui_path))

    if not ui_file.open(QIODevice.OpenModeFlag.ReadOnly):
        raise RuntimeError("Не удалось открыть файл main_window.ui")

    # Загружаем интерфейс
    window = loader.load(ui_file)
    ui_file.close()

    if window is None:
        raise RuntimeError("Не удалось загрузить интерфейс")

    # Загружаем логотип FinTrack
    logo_path = BASE_DIR / "resources" / "logo.png"

    logo_label = window.findChild(QLabel, "logoLabel")

    if logo_label and logo_path.exists():
        logo_label.setPixmap(QPixmap(logo_path))
        logo_label.setScaledContents(True)

    # Подключаем управление
    # Подключаем управление
    window.categories_controller = CategoriesPageController(window)
    window.dashboard_controller = DashboardPageController(window)
    window.budget_controller = BudgetPageController(window)
    window.analytics_controller = AnalyticsPageController(window)
    window.transactions_controller = TransactionsPageController(window)
    window.reports_controller = ReportsPageController(window)

    # Основной переключатель страниц
    stacked_pages = window.findChild(QStackedWidget, "stackedPages")

    if stacked_pages is None:
        raise RuntimeError("Не найден stackedPages")

    # Находим страницы
    pages = {
        "dashboard": window.findChild(QWidget, "page"),
        "transactions": window.findChild(QWidget, "pageTransactions"),
        "categories": window.findChild(QWidget, "pageCategories"),
        "budget": window.findChild(QWidget, "pageBudget"),
        "analytics": window.findChild(QWidget, "pageAnalytics"),
        "reports": window.findChild(QWidget, "pageReports")
    }

    navigation = {
        "btnDashboard": "dashboard",
        "btnTransactions": "transactions",
        "btnCategories": "categories",
        "btnBudget": "budget",
        "btnAnalytics": "analytics",
        "btnReports": "reports"
    }

    buttons = {}

    for button_name in navigation:
        button = window.findChild(QPushButton, button_name)

        if button is None:
            raise RuntimeError(f"Не найдена кнопка {button_name}")

        buttons[button_name] = button
        button.setProperty("active", False)

    for page_name, page in pages.items():
        if page is None:
            raise RuntimeError(f"Не найдена страница {page_name}")

    # Обновляем подсветку активной кнопки
    def set_active_button(active_name):
        for name, button in buttons.items():
            if name == active_name:
                button.setStyleSheet("""
                    background-color: #4B6688;
                    color: white;
                    font-weight: bold;
                """)
            else:
                button.setStyleSheet("")

    # Перключаем страницу и активную кнопку
    def navigate(page_name, button_name):
        stacked_pages.setCurrentWidget(pages[page_name])
        set_active_button(button_name)

    # Подключаем кнопки навигации
    for button_name, page_name in navigation.items():
        buttons[button_name].clicked.connect(
            lambda checked=False, p=page_name, b=button_name:
            navigate(p, b)
        )

    # Горячая клавиша для добавления операции
    add_transaction_shortcut = QShortcut(
        QKeySequence("Ctrl+N"),
        window
    )

    add_transaction_button = window.findChild(
        QPushButton,
        "btnAddNewTransaction"
    )

    if add_transaction_button is not None:
        add_transaction_shortcut.activated.connect(
            add_transaction_button.click
        )
    # Начальное состояние
    navigate("dashboard", "btnDashboard")

    # Показываем окно
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
