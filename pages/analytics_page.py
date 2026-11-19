
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QVBoxLayout

from PySide6.QtCharts import (
    QChart,
    QChartView,
    QBarSeries,
    QBarSet,
    QBarCategoryAxis,
    QValueAxis,
    QPieSeries
)

from database.analytics_manager import (
    get_period_summary,
    get_expenses_by_category,
    get_monthly_trend
)


class AnalyticsPageController:

    def __init__(self, window):
        self.window = window

        # Переключатель периода
        self.period_combo = window.findChild(
            object, "cmbAnalyticsPeriod"
        )

        # Карточки финансовых показателей
        self.income_label = window.findChild(
            object, "lblAnalyticsIncomeValue"
        )

        self.expense_label = window.findChild(
            object, "lblAnalyticsExpenseValue"
        )

        self.balance_label = window.findChild(
            object, "lblAnalyticsBalanceValue"
        )

        # Области графиков
        self.trend_widget = window.findChild(
            object, "analyticsChartWidget"
        )

        self.categories_widget = window.findChild(
            object, "analyticsCategoriesChartWidget"
        )

        widgets = [
            self.period_combo,
            self.income_label,
            self.expense_label,
            self.balance_label,
            self.trend_widget,
            self.categories_widget
        ]

        if any(widget is None for widget in widgets):
            raise RuntimeError(
                "Не удалось найти все элементы страницы аналитики."
            )

        # Настраиваем переключатель периода
        self.setup_period_filter()

        # Создаём области для графиков
        self.setup_chart_layouts()

        # Обновляем аналитику при смене периода
        self.period_combo.currentIndexChanged.connect(
            self.refresh
        )

        self.refresh()

    def setup_period_filter(self):
        """Настраивает варианты периода аналитики."""

        self.period_combo.blockSignals(True)
        self.period_combo.clear()

        self.period_combo.addItem(
            "Последние 3 месяца", 3
        )

        self.period_combo.addItem(
            "Последние 6 месяцев", 6
        )

        self.period_combo.addItem(
            "Последние 12 месяцев", 12
        )

        self.period_combo.setCurrentIndex(1)

        self.period_combo.blockSignals(False)

    def setup_chart_layouts(self):
        """Создаёт компоновки для графиков."""

        if self.trend_widget.layout() is None:
            self.trend_layout = QVBoxLayout(
                self.trend_widget
            )
        else:
            self.trend_layout = self.trend_widget.layout()

        if self.categories_widget.layout() is None:
            self.categories_layout = QVBoxLayout(
                self.categories_widget
            )
        else:
            self.categories_layout = (
                self.categories_widget.layout()
            )

        self.trend_layout.setContentsMargins(0, 0, 0, 0)
        self.categories_layout.setContentsMargins(0, 0, 0, 0)

        self.trend_chart_view = QChartView()
        self.categories_chart_view = QChartView()

        self.trend_chart_view.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        self.categories_chart_view.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        self.trend_chart_view.setStyleSheet(
            "background-color: white; border: none;"
        )

        self.categories_chart_view.setStyleSheet(
            "background-color: white; border: none;"
        )

        self.trend_layout.addWidget(
            self.trend_chart_view
        )

        self.categories_layout.addWidget(
            self.categories_chart_view
        )

    @staticmethod
    def format_amount(amount):
        """Форматирует денежную сумму."""

        return (
            f"{amount:,.2f}"
            .replace(",", " ")
            .replace(".", ",")
            + " ₽"
        )

    @staticmethod
    def get_start_date(months):
        """Вычисляет начало выбранного периода."""

        today = date.today()

        month_index = today.month - months + 1
        year = today.year

        while month_index <= 0:
            month_index += 12
            year -= 1

        return date(year, month_index, 1).isoformat()

    def refresh(self):
        """Обновляет карточки и графики аналитики."""

        months = self.period_combo.currentData()

        if months is None:
            return

        start_date = self.get_start_date(months)
        end_date = date.today().isoformat()

        summary = get_period_summary(
            start_date,
            end_date
        )

        # Обновляем карточки
        self.income_label.setText(
            self.format_amount(summary["income"])
        )

        self.expense_label.setText(
            self.format_amount(summary["expense"])
        )

        self.balance_label.setText(
            self.format_amount(summary["balance"])
        )

        # Получаем данные для графиков
        monthly_data = get_monthly_trend(months)

        category_data = get_expenses_by_category(
            start_date,
            end_date
        )

        self.update_trend_chart(monthly_data)
        self.update_categories_chart(category_data)

    def update_trend_chart(self, monthly_data):
        """Строит график доходов и расходов."""

        chart = QChart()
        chart.setTitle("Доходы и расходы")
        chart.setAnimationOptions(
            QChart.AnimationOption.SeriesAnimations
        )
        chart.setBackgroundBrush(
            QColor("#FFFFFF")
        )

        income_set = QBarSet("Доходы")
        expense_set = QBarSet("Расходы")

        income_set.setColor(
            QColor("#16A34A")
        )

        expense_set.setColor(
            QColor("#DC2626")
        )

        categories = []

        for item in monthly_data:
            categories.append(item["month"])
            income_set.append(item["income"])
            expense_set.append(item["expense"])

        series = QBarSeries()
        series.append(income_set)
        series.append(expense_set)

        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsAngle(-45)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%.0f")
        axis_y.setMin(0)

        chart.addAxis(
            axis_x,
            Qt.AlignmentFlag.AlignBottom
        )

        chart.addAxis(
            axis_y,
            Qt.AlignmentFlag.AlignLeft
        )

        chart.setBackgroundRoundness(8)

        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(
            Qt.AlignmentFlag.AlignBottom
        )

        self.trend_chart_view.setChart(chart)

    def update_categories_chart(self, category_data):
        """Строит круговую диаграмму расходов."""

        chart = QChart()
        chart.setTitle("Расходы по категориям")
        chart.setBackgroundBrush(
            QColor("#FFFFFF")
        )

        series = QPieSeries()

        for category in category_data:
            series.append(
                category["category_name"],
                float(category["total"])
            )

        chart.addSeries(series)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(
            Qt.AlignmentFlag.AlignBottom
        )

        if not category_data:
            chart.setTitle(
                "Расходы по категориям: данных пока нет"
            )

        self.categories_chart_view.setChart(chart)
