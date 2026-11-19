from datetime import date
from sqlite3 import Error as SQLiteError

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor
from PySide6.QtWidgets import (
    QMessageBox,
    QAbstractItemView,
    QProgressBar,
    QWidget,
    QVBoxLayout
)

from database.budget_manager import (
    get_budgets,
    add_budget,
    update_budget,
    delete_budget
)

from dialogs.budget_dialog import BudgetDialog


class BudgetPageController:

    def __init__(self, window):
        self.window = window

        # Элементы выбора периода
        self.month_combo = window.findChild(
            object, "cmbBudgetMonth"
        )

        self.year_combo = window.findChild(
            object, "cmbBudgetYear"
        )

        # Карточки бюджета
        self.limit_label = window.findChild(
            object, "lblBudgetLimitValue"
        )

        self.spent_label = window.findChild(
            object, "lblBudgetSpentValue"
        )

        self.remaining_label = window.findChild(
            object, "lblBudgetRemainingValue"
        )

        # Таблица бюджетов
        self.table = window.findChild(
            object, "tableBudgets"
        )

        # Кнопки управления
        self.btn_add = window.findChild(
            object, "btnAddBudget"
        )

        self.btn_edit = window.findChild(
            object, "btnEditBudget"
        )

        self.btn_delete = window.findChild(
            object, "btnDeleteBudget"
        )

        widgets = [
            self.month_combo,
            self.year_combo,
            self.limit_label,
            self.spent_label,
            self.remaining_label,
            self.table,
            self.btn_add,
            self.btn_edit,
            self.btn_delete
        ]

        if any(widget is None for widget in widgets):
            raise RuntimeError(
                "Не удалось найти все элементы страницы бюджета."
            )

        # Заполняем выбор месяца и года
        self.setup_period_filters()

        # Настраиваем таблицу
        self.model = QStandardItemModel()

        self.model.setHorizontalHeaderLabels([
            "ID",
            "Категория",
            "Лимит",
            "Потрачено",
            "Остаток",
            "Использовано",
            "Статус"
        ])

        self.table.setModel(self.model)
        self.table.setColumnHidden(0, True)

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.setSortingEnabled(False)
        self.table.horizontalHeader().setStretchLastSection(True)

        # Подключаем сигналы
        self.month_combo.currentIndexChanged.connect(
            self.refresh
        )

        self.year_combo.currentIndexChanged.connect(
            self.refresh
        )

        self.btn_add.clicked.connect(
            self.add_new_budget
        )

        self.btn_edit.clicked.connect(
            self.edit_selected_budget
        )

        self.btn_delete.clicked.connect(
            self.delete_selected_budget
        )

        self.table.selectionModel().selectionChanged.connect(
            self.update_action_buttons
        )

        self.update_action_buttons()
        self.refresh()

    def setup_period_filters(self):
        """Настраивает списки месяцев и годов."""

        month_names = [
            "Январь", "Февраль", "Март",
            "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь",
            "Октябрь", "Ноябрь", "Декабрь"
        ]

        current_date = date.today()

        self.month_combo.blockSignals(True)
        self.month_combo.clear()

        for month_number, month_name in enumerate(
            month_names, start=1
        ):
            self.month_combo.addItem(
                month_name,
                month_number
            )

        self.month_combo.setCurrentIndex(
            current_date.month - 1
        )
        self.month_combo.blockSignals(False)

        self.year_combo.blockSignals(True)
        self.year_combo.clear()

        for year in range(
            current_date.year - 3,
            current_date.year + 3
        ):
            self.year_combo.addItem(
                str(year),
                year
            )

        self.year_combo.setCurrentIndex(
            self.year_combo.findData(current_date.year)
        )

        self.year_combo.blockSignals(False)

    @staticmethod
    def format_amount(amount):
        """Форматирует денежную сумму."""

        return (
            f"{amount:,.2f}"
            .replace(",", " ")
            .replace(".", ",")
            + " ₽"
        )

    def get_selected_period(self):
        return (
            self.month_combo.currentData(),
            self.year_combo.currentData()
        )

    def refresh(self):
        """Обновляет таблицу и карточки бюджета."""

        month, year = self.get_selected_period()

        if month is None or year is None:
            return

        budgets = get_budgets(month, year)

        self.model.removeRows(0, self.model.rowCount())

        total_limit = 0
        total_spent = 0

        for budget in budgets:
            limit = float(budget["budget_amount"])
            spent = float(budget["spent"])
            remaining = limit - spent
            total_limit += limit
            total_spent += spent

            if limit > 0:
                usage_percent = spent / limit * 100
            else:
                usage_percent = 100 if spent > 0 else 0

            if spent > limit:
                status = "Превышен"
                status_color = "#DC2626"
                bar_color = "#DC2626"
            elif usage_percent >= 80:
                status = "Внимание"
                status_color = "#D97706"
                bar_color = "#D97706"
            else:
                status = "В норме"
                status_color = "#16A34A"
                bar_color = "#16A34A"

            usage_text = (
                f"{usage_percent:.0f}%"
                if limit > 0
                else ("Нет лимита" if spent > 0 else "0%")
            )

            row = [
                QStandardItem(str(budget["id"])),
                QStandardItem(budget["category_name"]),
                QStandardItem(f"{limit:.2f} ₽"),
                QStandardItem(f"{spent:.2f} ₽"),
                QStandardItem(f"{remaining:.2f} ₽"),
                QStandardItem(usage_text),
                QStandardItem(status)
            ]

            row[6].setForeground(QColor(status_color))

            row[0].setData(
                dict(budget),
                Qt.ItemDataRole.UserRole
            )

            self.model.appendRow(row)

            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(min(round(usage_percent), 100))
            progress.setFormat(usage_text)
            progress.setTextVisible(True)
            progress.setFixedHeight(22)

            progress.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #E2E8F0;
                    border-radius: 5px;
                    background-color: #F1F5F9;
                    color: #263B59;
                    text-align: center;
                    font-size: 11px;
                    padding: 0px;
                }}

                QProgressBar::chunk {{
                    background-color: {bar_color};
                    border-radius: 4px;
                }}
            """)

            progress_container = QWidget()
            progress_layout = QVBoxLayout(progress_container)

            progress_layout.setContentsMargins(4, 0, 4, 0)
            progress_layout.setSpacing(0)

            progress_layout.addStretch()
            progress_layout.addWidget(progress)
            progress_layout.addStretch()

            self.table.setIndexWidget(
                self.model.index(self.model.rowCount() - 1, 5),
                progress_container
            )

            self.table.setRowHeight(
                self.model.rowCount() - 1,
                36
            )

        total_remaining = total_limit - total_spent
        self.limit_label.setText(
            self.format_amount(total_limit)
        )

        self.spent_label.setText(
            self.format_amount(total_spent)
        )

        self.remaining_label.setText(
            self.format_amount(total_remaining)
        )

        self.table.resizeColumnsToContents()
        self.table.setColumnHidden(0, True)
        self.table.setColumnWidth(5, 130)
        self.table.setColumnWidth(6, 110)

        self.update_action_buttons()

    def get_selected_budget(self):
        selected = self.table.selectionModel().selectedRows()

        if not selected:
            return None

        row = selected[0].row()

        return self.model.item(
            row, 0
        ).data(Qt.ItemDataRole.UserRole)

    def update_action_buttons(self):
        has_selection = bool(
            self.table.selectionModel().selectedRows()
        )

        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)

    def add_new_budget(self):
        month, year = self.get_selected_period()

        dialog = BudgetDialog(
            self.window,
            month=month,
            year=year
        )

        if dialog.exec():
            data = dialog.get_data()

            try:
                add_budget(
                    category_id=data["category_id"],
                    amount=data["amount"],
                    month=month,
                    year=year
                )

                self.refresh()

            except (ValueError, SQLiteError) as error:
                QMessageBox.warning(
                    self.window,
                    "Ошибка",
                    str(error)
                )

    def edit_selected_budget(self):
        budget = self.get_selected_budget()

        if budget is None:
            return

        month, year = self.get_selected_period()

        dialog = BudgetDialog(
            self.window,
            month=month,
            year=year,
            budget=budget
        )

        if dialog.exec():
            data = dialog.get_data()

            try:
                update_budget(
                    budget_id=budget["id"],
                    amount=data["amount"]
                )

                self.refresh()

            except (ValueError, SQLiteError) as error:
                QMessageBox.warning(
                    self.window,
                    "Ошибка",
                    str(error)
                )

    def delete_selected_budget(self):
        budget = self.get_selected_budget()

        if budget is None:
            return

        answer = QMessageBox.question(
            self.window,
            "Удаление бюджета",
            "Вы действительно хотите удалить выбранный бюджет?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            delete_budget(budget["id"])
            self.refresh()

        except (ValueError, SQLiteError) as error:
            QMessageBox.warning(
                self.window,
                "Ошибка",
                str(error)
            )
