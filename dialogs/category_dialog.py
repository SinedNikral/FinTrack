
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDialogButtonBox,
    QLabel
)


class CategoryDialog(QDialog):
    def __init__(self, parent=None, category=None):
        super().__init__(parent)

        self.category = category
        self.is_editing = category is not None

        if self.is_editing:
            self.setWindowTitle("Изменение категории")
        else:
            self.setWindowTitle("Добавление категории")

        self.setMinimumWidth(350)

        # Основной макет
        main_layout = QVBoxLayout(self)

        # Заголовок
        if self.is_editing:
            title = QLabel("Изменение категории")
        else:
            title = QLabel("Новая категория")

        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #263B59;
            padding: 5px;
        """)

        main_layout.addWidget(title)

        # Форма
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Введите название категории")
        self.name_input.setMinimumHeight(35)

        self.type_combo = QComboBox()
        self.type_combo.addItem("Доходы", "income")
        self.type_combo.addItem("Расходы", "expense")
        self.type_combo.setMinimumHeight(35)

        form_layout.addRow("Название:", self.name_input)
        form_layout.addRow("Тип:", self.type_combo)

        main_layout.addLayout(form_layout)

        # Заполняем данные при редактировании
        if self.is_editing:
            self.name_input.setText(category["name"])

            index = self.type_combo.findData(category["type"])
            self.type_combo.setCurrentIndex(index)

            # Тип существующей категории менять нельзя
            self.type_combo.setEnabled(False)

        # Кнопки
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        main_layout.addWidget(self.buttons)

    def get_data(self):
        """Возвращает введённые данные."""

        return {
            "name": self.name_input.text().strip(),
            "type": self.type_combo.currentData()
        }
