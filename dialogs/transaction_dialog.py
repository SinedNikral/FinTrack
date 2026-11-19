from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QDoubleSpinBox,
    QDateEdit,
    QDialogButtonBox,
    QLabel,
    QTextEdit
)
from PySide6.QtCore import QDate

from database.category_manager import get_categories


class TransactionDialog(QDialog):
    def __init__(self, parent=None, transaction=None):
        super().__init__(parent)

        self.transaction = transaction
        self.is_editing = transaction is not None

        self.setWindowTitle(
            "Изменение операции"
            if self.is_editing
            else "Добавление операции"
        )
        self.setMinimumWidth(400)

        main_layout = QVBoxLayout(self)

        title = QLabel(
            "Изменение операции"
            if self.is_editing
            else "Новая операция"
        )
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #263B59;
            padding: 5px;
        """)
        main_layout.addWidget(title)

        form_layout = QFormLayout()

        # Тип операции
        self.type_combo = QComboBox()
        self.type_combo.addItem("Доход", "income")
        self.type_combo.addItem("Расход", "expense")
        self.type_combo.setMinimumHeight(35)

        # Сумма
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, 999999999.99)
        self.amount_input.setDecimals(2)
        self.amount_input.setSingleStep(100)
        self.amount_input.setSuffix(" ₽")
        self.amount_input.setMinimumHeight(35)

        # Категория
        self.category_combo = QComboBox()
        self.category_combo.setMinimumHeight(35)

        # Дата
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd.MM.yyyy")
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setMinimumHeight(35)

        # Описание
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText(
            "Дополнительная информация..."
        )
        self.description_input.setMaximumHeight(85)

        form_layout.addRow("Тип операции:", self.type_combo)
        form_layout.addRow("Сумма:", self.amount_input)
        form_layout.addRow("Категория:", self.category_combo)
        form_layout.addRow("Дата:", self.date_input)
        form_layout.addRow("Описание:", self.description_input)

        main_layout.addLayout(form_layout)

        # Обновление категорий при изменении типа
        self.type_combo.currentIndexChanged.connect(
            self.load_categories
        )

        # Загружаем исходные данные при редактировании
        if self.is_editing:
            self.type_combo.setCurrentIndex(
                self.type_combo.findData(transaction["type"])
            )
            self.amount_input.setValue(float(transaction["amount"]))

        self.load_categories()

        if self.is_editing:
            category_index = self.category_combo.findData(
                transaction["category_id"]
            )

            if category_index >= 0:
                self.category_combo.setCurrentIndex(category_index)

            transaction_date = QDate.fromString(
                transaction["transaction_date"],
                "yyyy-MM-dd"
            )

            if transaction_date.isValid():
                self.date_input.setDate(transaction_date)

            self.description_input.setPlainText(
                transaction["description"] or ""
            )

        # Кнопки
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        main_layout.addWidget(self.buttons)

    def load_categories(self):
        """Загружает категории выбранного типа."""

        category_type = self.type_combo.currentData()

        self.category_combo.clear()

        categories = get_categories(category_type)

        for category in categories:
            self.category_combo.addItem(
                category["name"],
                category["id"]
            )

    def get_data(self):
        """Возвращает данные операции."""

        return {
            "type": self.type_combo.currentData(),
            "amount": self.amount_input.value(),
            "category_id": self.category_combo.currentData(),
            "transaction_date": self.date_input.date().toString(
                "yyyy-MM-dd"
            ),
            "description": self.description_input.toPlainText().strip()
        }

    def accept(self):
        """Проверяет данные перед закрытием окна."""

        if self.category_combo.currentData() is None:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self,
                "Ошибка",
                "Для выбранного типа операции нет доступных категорий."
            )
            return

        super().accept()
