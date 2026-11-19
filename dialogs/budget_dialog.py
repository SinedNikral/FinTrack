
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QDialogButtonBox,
    QMessageBox
)

from database.category_manager import get_categories


class BudgetDialog(QDialog):

    def __init__(self, parent=None, month=1, year=2026, budget=None):
        super().__init__(parent)

        self.budget = budget
        self.is_editing = budget is not None

        self.month = month
        self.year = year

        self.setWindowTitle(
            "Изменение бюджета"
            if self.is_editing
            else "Добавление бюджета"
        )

        self.setMinimumWidth(380)

        main_layout = QVBoxLayout(self)

        title = QLabel(
            "Изменение бюджетного лимита"
            if self.is_editing
            else "Новый бюджет"
        )

        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #263B59;
            padding: 5px;
        """)

        main_layout.addWidget(title)

        form_layout = QFormLayout()

        # Категория расходов
        self.category_combo = QComboBox()
        self.category_combo.setMinimumHeight(35)

        categories = get_categories("expense")

        for category in categories:
            self.category_combo.addItem(
                category["name"],
                category["id"]
            )

        # Сумма бюджета
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 999999999.99)
        self.amount_input.setDecimals(2)
        self.amount_input.setSingleStep(500)
        self.amount_input.setSuffix(" ₽")
        self.amount_input.setMinimumHeight(35)

        # Период бюджета
        month_names = [
            "Январь", "Февраль", "Март",
            "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь",
            "Октябрь", "Ноябрь", "Декабрь"
        ]

        self.period_label = QLabel(
            f"{month_names[month - 1]} {year}"
        )

        form_layout.addRow(
            "Категория:",
            self.category_combo
        )

        form_layout.addRow(
            "Лимит:",
            self.amount_input
        )

        form_layout.addRow(
            "Период:",
            self.period_label
        )

        main_layout.addLayout(form_layout)

        # Заполнение при редактировании
        if self.is_editing:
            category_index = self.category_combo.findData(
                budget["category_id"]
            )

            if category_index >= 0:
                self.category_combo.setCurrentIndex(category_index)

            self.category_combo.setEnabled(False)

            self.amount_input.setValue(
                float(budget["budget_amount"])
            )

        # Кнопки
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        main_layout.addWidget(self.buttons)

    def get_data(self):
        return {
            "category_id": self.category_combo.currentData(),
            "amount": self.amount_input.value()
        }

    def accept(self):
        if self.category_combo.currentData() is None:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Нет доступных категорий расходов."
            )
            return

        super().accept()
