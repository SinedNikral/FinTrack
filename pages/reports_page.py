from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QStandardItemModel, QStandardItem, QDesktopServices
from PySide6.QtWidgets import QMessageBox, QPushButton

from database.transaction_manager import get_transactions
from database.analytics_manager import get_expenses_by_category
from database.report_history_manager import (
    get_reports,
    delete_report
    )

from dialogs.report_dialog import ReportDialog
from pathlib import Path


class ReportsPageController:

    def __init__(self, window):
        self.window = window

        # Элементы страницы отчётов
        self.report_type_combo = window.findChild(
            object, "cmbReportsType"
        )

        self.date_from = window.findChild(
            object, "dateReportsFrom"
        )

        self.date_to = window.findChild(
            object, "dateReportsTo"
        )

        self.generate_button = window.findChild(
            object, "btnGenerateReport"
        )

        self.history_table = window.findChild(
            object, "tableReportsHistory"
        )

        widgets = [
            self.report_type_combo,
            self.date_from,
            self.date_to,
            self.generate_button,
            self.history_table
        ]

        if any(widget is None for widget in widgets):
            raise RuntimeError(
                "Не удалось найти все элементы страницы отчётов."
            )

        # Подключаем кнопку формирования отчёта
        self.generate_button.clicked.connect(
            self.generate_report
        )

        self.setup_history_table()
        self.refresh_history()

        self.delete_button = self.window.findChild(
            QPushButton,
            "btnDeleteReport"
        )

        self.delete_button.clicked.connect(
            self.delete_selected_report
        )

    def generate_report(self):
        """Формирует отчёт за выбранный период."""

        report_type = self.report_type_combo.currentText()

        date_from = self.date_from.date().toString(
            "yyyy-MM-dd"
        )

        date_to = self.date_to.date().toString(
            "yyyy-MM-dd"
        )

        # Проверяем корректность периода
        if date_from > date_to:
            QMessageBox.warning(
                self.window,
                "Некорректный период",
                "Начальная дата не может быть позже конечной."
            )
            return

        # Определяем тип операций
        transaction_type = None

        if report_type == "Отчёт по доходам":
            transaction_type = "income"

        elif report_type == "Отчёт по расходам":
            transaction_type = "expense"

        elif report_type not in [
            "Общий финансовый отчёт",
            "Отчёт по категориям"
        ]:
            QMessageBox.warning(
                self.window,
                "Ошибка",
                "Выбран неизвестный тип отчёта."
            )
            return

        # Получаем операции за выбранный период
        transactions = get_transactions(
            transaction_type=transaction_type,
            date_from=date_from,
            date_to=date_to
        )

        # Для отчёта по категориям получаем отдельную сводку
        category_data = []

        if report_type == "Отчёт по категориям":
            category_data = get_expenses_by_category(
                date_from,
                date_to
            )

        # Открываем окно просмотра отчёта
        dialog = ReportDialog(
            report_type=report_type,
            date_from=self.date_from.date().toString(
                "dd.MM.yyyy"
            ),
            date_to=self.date_to.date().toString(
                "dd.MM.yyyy"
            ),
            transactions=transactions,
            category_data=category_data,
            parent=self.window
        )

        dialog.report_exported.connect(
            self.refresh_history
        )

        dialog.exec()

    def setup_history_table(self):
        """Настраивает таблицу истории отчётов."""

        self.history_model = QStandardItemModel()

        self.history_model.setHorizontalHeaderLabels([
            "ID",
            "Тип отчёта",
            "Период",
            "Формат",
            "Дата создания"
        ])

        self.history_table.setModel(self.history_model)

        # Скрываем технический столбец ID
        self.history_table.setColumnHidden(0, True)

        # Выравнивание заголовков
        self.history_table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        # Растягиваем последний столбец
        self.history_table.horizontalHeader().setStretchLastSection(
            True
        )

        # Выравнивание содержимого ячеек
        self.history_table.setColumnWidth(1, 220)
        self.history_table.setColumnWidth(2, 200)
        self.history_table.setColumnWidth(3, 100)

        # Выбор целой строки
        self.history_table.setSelectionBehavior(
            self.history_table.SelectionBehavior.SelectRows
        )

        # Запрещаем редактирование ячеек
        self.history_table.setEditTriggers(
            self.history_table.EditTrigger.NoEditTriggers
        )

        # Чередование цветов строк
        self.history_table.setAlternatingRowColors(True)

        # Включаем сортировку по заголовкам
        self.history_table.setSortingEnabled(True)

        # Высота строк
        self.history_table.verticalHeader().setDefaultSectionSize(
            38
        )

        # Скрываем нумерацию строк
        self.history_table.verticalHeader().setVisible(False)

        # Открытие отчёта двойным щелчком
        self.history_table.doubleClicked.connect(
            self.open_report_file
        )

    def refresh_history(self):
        """Загружает историю отчётов из базы данных."""

        reports = get_reports()

        self.history_model.setRowCount(0)

        for report in reports:

            period = (
                f'{report["date_from"]} — '
                f'{report["date_to"]}'
            )

            created_at = report["created_at"]

            id_item = QStandardItem(str(report["id"]))
            type_item = QStandardItem(report["report_type"])
            period_item = QStandardItem(period)
            format_item = QStandardItem(report["file_format"])
            date_item = QStandardItem(created_at)

            # Сохраняем дату для корректной сортировки
            date_item.setData(
                created_at,
                Qt.ItemDataRole.UserRole
            )

            items = [
                id_item,
                type_item,
                period_item,
                format_item,
                date_item
            ]

            self.history_model.appendRow(items)

        self.history_table.resizeColumnsToContents()

    def open_report_file(self, index):
        """Открывает сохранённый файл отчёта."""

        report_id_item = self.history_model.item(
            index.row(), 0
        )

        report_id = int(report_id_item.text())

        reports = get_reports()

        selected_report = next(
            (
                report for report in reports
                if report["id"] == report_id
            ),
            None
        )

        if selected_report is None:
            return

        file_path = selected_report["file_path"]

        # Проверяем, существует ли файл
        if not Path(file_path).is_file():
            QMessageBox.warning(
                self.window,
                "Файл не найден",
                "Файл отчёта не существует.\n\n"
                "Возможно, он был перемещён или удалён."
            )
            return

        # Открываем файл
        if not QDesktopServices.openUrl(
            QUrl.fromLocalFile(file_path)
        ):
            QMessageBox.warning(
                self.window,
                "Ошибка",
                "Не удалось открыть файл отчёта."
            )

    def delete_selected_report(self):
        """Удаляет выбранную запись из истории отчётов."""

        selected_rows = (
            self.history_table.selectionModel().selectedRows()
        )

        if not selected_rows:
            QMessageBox.information(
                self.window,
                "Удаление записи",
                "Сначала выберите отчёт в таблице."
            )
            return

        row = selected_rows[0].row()

        report_id = int(
            self.history_model.item(row, 0).text()
        )

        answer = QMessageBox.question(
            self.window,
            "Подтверждение удаления",
            "Удалить выбранную запись из истории отчётов?\n\n"
            "Сам файл отчёта останется на компьютере.",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        delete_report(report_id)

        self.refresh_history()

        QMessageBox.information(
            self.window,
            "Готово",
            "Запись успешно удалена из истории."
        )
