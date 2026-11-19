
from PySide6.QtWidgets import (
    QPushButton,
    QTableView,
    QMessageBox,
    QAbstractItemView,
    QHeaderView
)

from PySide6.QtGui import QStandardItemModel, QStandardItem

from database.category_manager import (
    get_categories,
    add_category,
    update_category,
    delete_category
)

from dialogs.category_dialog import CategoryDialog


class CategoriesPageController:
    def __init__(self, window):
        self.window = window

        # Получаем элементы интерфейса
        self.table = window.findChild(QTableView, "tableCategories")

        self.btn_add = window.findChild(
            QPushButton, "btnAddCategory"
        )
        self.btn_edit = window.findChild(
            QPushButton, "btnEditCategory"
        )
        self.btn_delete = window.findChild(
            QPushButton, "btnDeleteCategory"
        )

        # Проверяем наличие элементов
        if any(widget is None for widget in (
            self.table,
            self.btn_add,
            self.btn_edit,
            self.btn_delete
        )):
            raise RuntimeError(
                "Не удалось найти элементы страницы категорий."
            )

        # Настраиваем таблицу
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        # Подключаем кнопки
        self.btn_add.clicked.connect(self.add_category)
        self.btn_edit.clicked.connect(self.edit_category)
        self.btn_delete.clicked.connect(self.remove_category)

        # Кнопки редактирования и удаления доступны
        # только при выборе категории
        self.btn_edit.setEnabled(False)
        self.btn_delete.setEnabled(False)

        self.load_categories()

    def load_categories(self):
        """Загружает категории из базы данных в таблицу."""

        categories = get_categories()

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels([
            "ID",
            "Название",
            "Тип",
            "Вид"
        ])

        for category in categories:
            category = dict(category)

            category_type = (
                "Доходы"
                if category["type"] == "income"
                else "Расходы"
            )

            category_kind = (
                "Стандартная"
                if category["is_default"]
                else "Пользовательская"
            )

            id_item = QStandardItem(str(category["id"]))
            name_item = QStandardItem(category["name"])
            type_item = QStandardItem(category_type)
            kind_item = QStandardItem(category_kind)

            # Сохраняем данные категории в первой ячейке
            id_item.setData(
                category,
                256
            )

            for item in (
                id_item,
                name_item,
                type_item,
                kind_item
            ):
                item.setEditable(False)

            model.appendRow([
                id_item,
                name_item,
                type_item,
                kind_item
            ])

        self.table.setModel(model)

        # Скрываем технический столбец ID
        self.table.hideColumn(0)

        # Настраиваем ширину столбцов
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        header.setStretchLastSection(True)

        # Отслеживаем выбор строки
        self.table.selectionModel().selectionChanged.connect(
            self.update_buttons
        )

        self.update_buttons()

    def get_selected_category(self):
        """Возвращает данные выбранной категории."""

        selection = self.table.selectionModel().selectedRows()

        if not selection:
            return None

        row = selection[0].row()

        return self.table.model().item(row, 0).data(256)

    def update_buttons(self, *args):
        """Управляет доступностью кнопок."""

        selected = self.get_selected_category() is not None

        self.btn_edit.setEnabled(selected)
        self.btn_delete.setEnabled(selected)

    def add_category(self):
        """Открывает окно добавления категории."""

        dialog = CategoryDialog(self.window)

        if dialog.exec():
            data = dialog.get_data()

            try:
                add_category(data["name"], data["type"])
                self.load_categories()

                QMessageBox.information(
                    self.window,
                    "Успешно",
                    "Категория добавлена."
                )

            except (ValueError, Exception) as error:
                QMessageBox.warning(
                    self.window,
                    "Ошибка",
                    str(error)
                )

    def edit_category(self):
        """Изменяет выбранную категорию."""

        category = self.get_selected_category()

        if category is None:
            return

        dialog = CategoryDialog(
            self.window,
            category
        )

        if dialog.exec():
            data = dialog.get_data()

            try:
                update_category(
                    category["id"],
                    data["name"]
                )

                self.load_categories()

                QMessageBox.information(
                    self.window,
                    "Успешно",
                    "Категория изменена."
                )

            except (ValueError, Exception) as error:
                QMessageBox.warning(
                    self.window,
                    "Ошибка",
                    str(error)
                )

    def remove_category(self):
        """Удаляет выбранную категорию."""

        category = self.get_selected_category()

        if category is None:
            return

        answer = QMessageBox.question(
            self.window,
            "Удаление категории",
            f"Вы действительно хотите удалить категорию "
            f"«{category['name']}»?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            delete_category(category["id"])
            self.load_categories()

            QMessageBox.information(
                self.window,
                "Успешно",
                "Категория удалена."
            )

        except (ValueError, Exception) as error:
            QMessageBox.warning(
                self.window,
                "Ошибка",
                str(error)
            )
