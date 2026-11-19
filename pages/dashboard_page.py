
from datetime import datetime

from PySide6.QtCore import Qt, QMargins
from PySide6.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QPainter,
    QColor,
    QBrush
)
from PySide6.QtWidgets import QAbstractItemView, QVBoxLayout
from PySide6.QtCharts import (
    QChart,
    QChartView,
    QBarSeries,
    QBarSet,
    QBarCategoryAxis,
    QValueAxis
)

from database.analytics_manager import get_monthly_trend
from database.transaction_manager import (
    get_transaction_summary,
    get_recent_transactions
)


class DashboardPageController:

    def __init__(self, window):
        self.window = window

        # Карточки главной страницы
        self.balance_label = window.findChild(
            object, "lblBalanceValue"
        )
        self.income_label = window.findChild(
            object, "lblIncomeValue"
        )
        self.expense_label = window.findChild(
            object, "lblExpenseValue"
        )

        # Таблица последних операций
        self.table = window.findChild(
            object, "tableRecentTransactions"
        )

        self.chart_container = window.findChild(
            object, "dashboardTrendChartWidget"
        )

        self.chart_container.setMinimumHeight(250)
        self.chart_container.setMaximumHeight(270)

        widgets = [
            self.balance_label,
            self.income_label,
            self.expense_label,
            self.table,
            self.chart_container
        ]

        if any(widget is None for widget in widgets):
            raise RuntimeError(
                "Не удалось найти элементы главной страницы."
            )

        # Создаём модель таблицы
        self.model = QStandardItemModel()

        self.model.setHorizontalHeaderLabels([
            "Дата",
            "Тип",
            "Категория",
            "Сумма",
            "Описание"
        ])

        self.table.setModel(self.model)

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.setSortingEnabled(False)

        # Настройки заголовка таблицы
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setFixedHeight(36)

        # Настройки строк
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)

        # Ширина столбцов
        self.table.setColumnWidth(0, 100)  # Дата
        self.table.setColumnWidth(1, 80)   # Тип
        self.table.setColumnWidth(2, 160)  # Категория
        self.table.setColumnWidth(3, 130)  # Сумма
        # Описание автоматически займёт оставшееся место

        self.table.setAlternatingRowColors(True)

        # Создаём область для графика
        self.chart_layout = QVBoxLayout(self.chart_container)
        self.chart_layout.setContentsMargins(0, 0, 0, 0)

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        self.chart_view.setStyleSheet(
            "background-color: transparent; border: none;"
        )

        self.chart_layout.addWidget(self.chart_view)

        # Загружаем данные
        self.refresh()

    @staticmethod
    def format_amount(amount):
        """Форматирует сумму в российском формате."""

        return (
            f"{amount:,.2f}"
            .replace(",", " ")
            .replace(".", ",")
            + " ₽"
        )

    def refresh(self):
        """Обновляет все данные главной страницы."""

        self.update_summary()
        self.update_recent_transactions()
        self.update_trend_chart()

    def update_summary(self):
        """Обновляет финансовые показатели."""

        summary = get_transaction_summary()

        self.balance_label.setText(
            self.format_amount(summary["balance"])
        )

        self.income_label.setText(
            self.format_amount(summary["income"])
        )

        self.expense_label.setText(
            self.format_amount(summary["expense"])
        )

    def update_recent_transactions(self):
        """Обновляет таблицу последних операций."""

        transactions = get_recent_transactions(5)

        self.model.removeRows(0, self.model.rowCount())

        for transaction in transactions:

            transaction_date = datetime.strptime(
                transaction["transaction_date"],
                "%Y-%m-%d"
            ).strftime("%d.%m.%Y")

            transaction_type = (
                "Доход"
                if transaction["type"] == "income"
                else "Расход"
            )

            amount = self.format_amount(
                transaction["amount"]
            )

            row = [
                QStandardItem(transaction_date),
                QStandardItem(transaction_type),
                QStandardItem(transaction["category_name"]),
                QStandardItem(amount),
                QStandardItem(transaction["description"] or "")
            ]

            for item in row:
                item.setEditable(False)

            # Выравнивание суммы по правому краю
            row[3].setTextAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )

            # Цветовое выделение доходов и расходов
            if transaction["type"] == "income":
                row[1].setForeground(
                    QBrush(QColor("#16A34A"))
                )
                row[3].setForeground(
                    QBrush(QColor("#16A34A"))
                )
            else:
                row[1].setForeground(
                    QBrush(QColor("#DC2626"))
                )
                row[3].setForeground(
                    QBrush(QColor("#DC2626"))
                )

            self.model.appendRow(row)

        self.table.resizeColumnsToContents()

    def update_trend_chart(self):
        """Обновляет график доходов и расходов за последние 6 месяцев."""

        monthly_data = get_monthly_trend(6)

        income_set = QBarSet("Доходы")
        expense_set = QBarSet("Расходы")

        categories = []

        for item in monthly_data:
            categories.append(item["month"])
            income_set.append(float(item["income"]))
            expense_set.append(float(item["expense"]))

        # Создаём набор столбцов
        series = QBarSeries()
        series.append(income_set)
        series.append(expense_set)

        # Создаём график
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Доходы и расходы за 6 месяцев")
        chart.setBackgroundBrush(QColor("#FFFFFF"))
        chart.setPlotAreaBackgroundBrush(QColor("#FFFFFF"))
        chart.setPlotAreaBackgroundVisible(True)
        chart.setBackgroundRoundness(8)

        # Настраиваем внутренние отступы графика
        chart.setMargins(QMargins(25, 10, 20, 10))

        chart.legend().setVisible(True)
        chart.legend().setAlignment(
            Qt.AlignmentFlag.AlignBottom
        )

        # Горизонтальная ось — месяцы
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)

        chart.addAxis(
            axis_x,
            Qt.AlignmentFlag.AlignBottom
        )
        series.attachAxis(axis_x)

        # Вертикальная ось — суммы
        axis_y = QValueAxis()
        axis_y.setTitleText("Сумма, ₽")
        axis_y.setLabelFormat("%.0f")
        axis_y.setMin(0)

        max_value = max(
            [
                max(
                    float(item["income"]),
                    float(item["expense"])
                )
                for item in monthly_data
            ],
            default=0
        )

        axis_y.setMax(
            max_value * 1.15 if max_value > 0 else 100
        )

        chart.addAxis(
            axis_y,
            Qt.AlignmentFlag.AlignLeft
        )
        series.attachAxis(axis_y)

        # Цвета столбцов
        income_set.setColor(QColor("#16A34A"))
        expense_set.setColor(QColor("#DC2626"))

        # Устанавливаем график в интерфейс
        self.chart_view.setChart(chart)
