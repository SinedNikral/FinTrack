
from datetime import datetime

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (
    QTableView,
    QComboBox,
    QDateEdit,
    QPushButton,
    QMessageBox,
    QDialog,
    QHeaderView
)

from database.category_manager import get_categories
from database.transaction_manager import (
    get_transactions,
    add_transaction,
    update_transaction,
    delete_transaction
)
from database.budget_manager import get_budgets
from dialogs.transaction_dialog import TransactionDialog


class TransactionsPageController:
    def __init__(self, window):
        self.window = window

        # Получаем элементы интерфейса
        self.table = window.findChild(
            QTableView, "tableTransactions"
        )
        self.type_filter = window.findChild(
            QComboBox, "cmbTransactionType"
        )
        self.category_filter = window.findChild(
            QComboBox, "cmbTransactionCategory"
        )
        self.date_from = window.findChild(
            QDateEdit, "dateFrom"
        )
        self.date_to = window.findChild(
            QDateEdit, "dateTo"
        )

        self.btn_reset = window.findChild(
            QPushButton, "btnResetFilters"
        )
        self.btn_add = window.findChild(
            QPushButton, "btnAddNewTransaction"
        )
        self.btn_edit = window.findChild(
            QPushButton, "btnEditTransaction"
        )
        self.btn_delete = window.findChild(
            QPushButton, "btnDeleteTransaction"
        )

        required_widgets = {
            "tableTransactions": self.table,
            "cmbTransactionType": self.type_filter,
            "cmbTransactionCategory": self.category_filter,
            "dateFrom": self.date_from,
            "dateTo": self.date_to,
            "btnResetFilters": self.btn_reset,
            "btnAddNewTransaction": self.btn_add,
            "btnEditTransaction": self.btn_edit,
            "btnDeleteTransaction": self.btn_delete
        }

        missing = [
            name for name, widget in required_widgets.items()
            if widget is None
        ]

        if missing:
            raise RuntimeError(
                "Не найдены элементы интерфейса: "
                + ", ".join(missing)
            )

        self.setup_table()
        self.setup_filters()
        self.connect_signals()

        # Кнопки редактирования и удаления
        # доступны только при выборе операции
        self.update_action_buttons()

        # Кнопка быстрого добавления на главной странице
        self.dashboard_add_button = window.findChild(
            QPushButton, "btnAddTransaction"
        )

        if self.dashboard_add_button:
            self.dashboard_add_button.clicked.connect(
                self.add_new_transaction
            )

        self.load_transactions()

    def setup_table(self):
        """Настраивает таблицу операций."""

        self.model = QStandardItemModel()

        self.model.setHorizontalHeaderLabels([
            "ID",
            "Дата",
            "Тип",
            "Категория",
            "Сумма",
            "Описание"
        ])

        self.table.setModel(self.model)

        self.table.setColumnHidden(0, True)
        self.table.setSortingEnabled(False)

        self.table.setSelectionBehavior(
            QTableView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QTableView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QTableView.EditTrigger.NoEditTriggers
        )

        self.table.doubleClicked.connect(
            self.edit_selected_transaction
        )

        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setStretchLastSection(True)

        self.table.selectionModel().selectionChanged.connect(
            self.update_action_buttons
        )

    def setup_filters(self):
        """Настраивает фильтры."""

        # Тип операции
        self.type_filter.clear()
        self.type_filter.addItem("Все операции", None)
        self.type_filter.addItem("Доходы", "income")
        self.type_filter.addItem("Расходы", "expense")

        # Категории
        self.load_category_filter()

        # Диапазон дат
        self.date_from.setMinimumDate(QDate(2000, 1, 1))
        self.date_from.setDate(QDate(2000, 1, 1))

        self.date_to.setMinimumDate(QDate(2000, 1, 1))
        self.date_to.setDate(QDate.currentDate())

    def connect_signals(self):
        """Подключает сигналы элементов интерфейса."""

        self.type_filter.currentIndexChanged.connect(
            self.on_type_filter_changed
        )

        self.category_filter.currentIndexChanged.connect(
            self.load_transactions
        )

        self.date_from.dateChanged.connect(
            self.on_date_from_changed
        )
        self.date_to.dateChanged.connect(
            self.on_date_to_changed
        )

        self.btn_reset.clicked.connect(
            self.reset_filters
        )
        self.btn_add.clicked.connect(
            self.add_new_transaction
        )
        self.btn_edit.clicked.connect(
            self.edit_selected_transaction
        )
        self.btn_delete.clicked.connect(
            self.delete_selected_transaction
        )

    def load_category_filter(self):
        """Загружает категории с учётом выбранного типа."""

        selected_type = self.type_filter.currentData()

        self.category_filter.blockSignals(True)
        self.category_filter.clear()

        self.category_filter.addItem(
            "Все категории", None
        )

        categories = get_categories(selected_type)

        for category in categories:
            self.category_filter.addItem(
                category["name"],
                category["id"]
            )

        self.category_filter.blockSignals(False)

    def on_type_filter_changed(self):
        """Обновляет категории после смены типа операции."""

        self.load_category_filter()
        self.load_transactions()

    def on_date_from_changed(self, new_date):
        """Не позволяет начальной дате быть позже конечной."""

        if new_date > self.date_to.date():
            self.date_to.setDate(new_date)

        self.load_transactions()

    def on_date_to_changed(self, new_date):
        """Не позволяет конечной дате быть раньше начальной."""

        if new_date < self.date_from.date():
            self.date_from.setDate(new_date)

        self.load_transactions()

    def load_transactions(self):
        """Загружает операции в таблицу."""

        try:
            transactions = get_transactions(
                transaction_type=self.type_filter.currentData(),
                category_id=self.category_filter.currentData(),
                date_from=self.date_from.date().toString(
                    "yyyy-MM-dd"
                ),
                date_to=self.date_to.date().toString(
                    "yyyy-MM-dd"
                )
            )

            self.model.removeRows(
                0, self.model.rowCount()
            )

            for transaction in transactions:
                transaction = dict(transaction)

                date_value = datetime.strptime(
                    transaction["transaction_date"],
                    "%Y-%m-%d"
                ).strftime("%d.%m.%Y")

                type_value = (
                    "Доход"
                    if transaction["type"] == "income"
                    else "Расход"
                )

                amount_value = (
                    f'{transaction["amount"]:,.2f}'
                    .replace(",", " ")
                    .replace(".", ",")
                    + " ₽"
                )

                row = [
                    QStandardItem(str(transaction["id"])),
                    QStandardItem(date_value),
                    QStandardItem(type_value),
                    QStandardItem(transaction["category_name"]),
                    QStandardItem(amount_value),
                    QStandardItem(transaction["description"] or "")
                ]

                # Сохраняем полные данные операции
                # в первой ячейке строки
                row[0].setData(
                    transaction,
                    Qt.ItemDataRole.UserRole
                )

                self.model.appendRow(row)

            self.update_action_buttons()

        except Exception as error:
            QMessageBox.critical(
                self.window,
                "Ошибка",
                f"Не удалось загрузить операции:\n{error}"
            )

    def get_selected_transaction(self):
        """Возвращает данные выбранной операции."""

        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            return None

        row = selected_rows[0].row()

        return self.model.item(
            row, 0
        ).data(Qt.ItemDataRole.UserRole)

    def update_action_buttons(self, *args):
        """Управляет доступностью кнопок."""

        has_selection = (
            self.get_selected_transaction() is not None
        )

        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)

    def get_budget_snapshot(self, transaction_dates):
        """Получает состояние бюджетов за указанные месяцы."""

        months = set()

        for transaction_date in transaction_dates:
            parsed_date = datetime.strptime(
                transaction_date, "%Y-%m-%d"
            )

            months.add((
                parsed_date.month,
                parsed_date.year
            ))

        snapshot = {}

        for month, year in months:
            budgets = get_budgets(month, year)

            for budget in budgets:
                budget = dict(budget)

                key = (
                    budget["category_id"],
                    month,
                    year
                )

                snapshot[key] = {
                    "category_name": budget["category_name"],
                    "budget_amount": float(budget["budget_amount"]),
                    "spent": float(budget["spent"])
                }

        return snapshot

    def check_budget_alerts(self, before, after):
        """Показывает уведомления при достижении порогов бюджета."""

        for key, current in after.items():
            previous = before.get(key)

            if previous is None:
                continue

            budget_amount = current["budget_amount"]

            if budget_amount <= 0:
                continue

            old_spent = previous["spent"]
            new_spent = current["spent"]

            old_percent = old_spent / budget_amount * 100
            new_percent = new_spent / budget_amount * 100

            if old_percent < 100 <= new_percent:
                excess = new_spent - budget_amount

                QMessageBox.warning(
                    self.window,
                    "Бюджет превышен",
                    (
                        f'Категория: {current["category_name"]}\n'
                        f'Потрачено: {new_spent:,.2f} ₽\n'
                        f'Бюджет: {budget_amount:,.2f} ₽\n'
                        f'Превышение: {excess:,.2f} ₽'
                    ).replace(",", " ")
                )

            elif old_percent < 80 <= new_percent:
                QMessageBox.information(
                    self.window,
                    "Бюджет почти исчерпан",
                    (
                        f'Категория: {current["category_name"]}\n'
                        f'Использовано: {new_percent:.1f}% бюджета\n'
                        f'Потрачено: {new_spent:,.2f} ₽\n'
                        f'Бюджет: {budget_amount:,.2f} ₽'
                    ).replace(",", " ")
                )

    def add_new_transaction(self):
        """Открывает диалог добавления операции."""

        dialog = TransactionDialog(self.window)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        try:
            before = self.get_budget_snapshot([
                data["transaction_date"]
            ])

            add_transaction(
                data["type"],
                data["amount"],
                data["category_id"],
                data["transaction_date"],
                data["description"]
            )

            self.load_transactions()
            self.window.dashboard_controller.refresh()
            self.window.budget_controller.refresh()

            after = self.get_budget_snapshot([
                data["transaction_date"]
            ])

            self.check_budget_alerts(before, after)

        except Exception as error:
            QMessageBox.critical(
                self.window,
                "Ошибка",
                f"Не удалось добавить операцию:\n{error}"
            )

    def edit_selected_transaction(self):
        """Редактирует выбранную операцию."""

        transaction = self.get_selected_transaction()

        if transaction is None:
            return

        dialog = TransactionDialog(
            self.window,
            transaction
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        try:
            affected_dates = [
                transaction["transaction_date"],
                data["transaction_date"]
            ]

            before = self.get_budget_snapshot(affected_dates)

            update_transaction(
                transaction["id"],
                data["type"],
                data["amount"],
                data["category_id"],
                data["transaction_date"],
                data["description"]
            )

            self.load_transactions()
            self.window.dashboard_controller.refresh()
            self.window.budget_controller.refresh()

            after = self.get_budget_snapshot(affected_dates)

            self.check_budget_alerts(before, after)

        except Exception as error:
            QMessageBox.critical(
                self.window,
                "Ошибка",
                f"Не удалось изменить операцию:\n{error}"
            )

    def delete_selected_transaction(self):
        """Удаляет выбранную операцию."""

        transaction = self.get_selected_transaction()

        if transaction is None:
            return

        answer = QMessageBox.question(
            self.window,
            "Удаление операции",
            "Вы действительно хотите удалить выбранную операцию?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            delete_transaction(transaction["id"])
            self.load_transactions()
            self.window.dashboard_controller.refresh()
            self.window.budget_controller.refresh()

        except Exception as error:
            QMessageBox.critical(
                self.window,
                "Ошибка",
                f"Не удалось удалить операцию:\n{error}"
            )

    def reset_filters(self):
        """Сбрасывает все фильтры."""

        self.type_filter.setCurrentIndex(0)
        self.load_category_filter()

        self.date_from.setDate(QDate(2000, 1, 1))
        self.date_to.setDate(QDate.currentDate())

        self.load_transactions()
