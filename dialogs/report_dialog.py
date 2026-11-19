import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QFileDialog,
    QMessageBox
)

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from database.report_history_manager import add_report


class ReportDialog(QDialog):

    report_exported = Signal()

    def __init__(
        self,
        report_type,
        date_from,
        date_to,
        transactions,
        category_data=None,
        parent=None
    ):
        super().__init__(parent)

        self.report_type = report_type
        self.transactions = transactions
        self.category_data = category_data or []
        self.date_from = date_from
        self.date_to = date_to

        self.setWindowTitle("Просмотр отчёта")
        self.resize(850, 550)

        self.setup_ui(date_from, date_to)
        self.fill_table()

    def setup_ui(self, date_from, date_to):

        layout = QVBoxLayout(self)

        title = QLabel(self.report_type)
        title.setStyleSheet(
            "font-size: 20px; font-weight: bold;"
        )

        period = QLabel(
            f"Период: {date_from} — {date_to}"
        )

        layout.addWidget(title)
        layout.addWidget(period)

        self.summary_label = QLabel()
        self.summary_label.setStyleSheet(
            "font-size: 14px; padding: 8px;"
        )

        layout.addWidget(self.summary_label)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        layout.addWidget(self.table)

        buttons_layout = QHBoxLayout()

        self.excel_button = QPushButton("Сохранить в Excel")
        self.pdf_button = QPushButton("Сохранить в PDF")
        self.close_button = QPushButton("Закрыть")

        self.excel_button.clicked.connect(
            self.export_to_excel
        )

        self.pdf_button.clicked.connect(
            self.export_to_pdf
        )

        self.close_button.clicked.connect(self.accept)

        buttons_layout.addWidget(self.excel_button)
        buttons_layout.addWidget(self.pdf_button)

        buttons_layout.addStretch()

        buttons_layout.addWidget(self.close_button)

        layout.addLayout(buttons_layout)

    @staticmethod
    def format_amount(amount):
        return (
            f"{amount:,.2f}"
            .replace(",", " ")
            .replace(".", ",")
            + " ₽"
        )

    def fill_table(self):

        if self.report_type == "Отчёт по категориям":
            self.fill_category_table()
            return

        income = sum(
            float(row["amount"])
            for row in self.transactions
            if row["type"] == "income"
        )

        expense = sum(
            float(row["amount"])
            for row in self.transactions
            if row["type"] == "expense"
        )

        balance = income - expense

        self.summary_label.setText(
            f"Доходы: {self.format_amount(income)}    "
            f"Расходы: {self.format_amount(expense)}    "
            f"Баланс: {self.format_amount(balance)}"
        )

        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Дата",
            "Тип",
            "Категория",
            "Сумма",
            "Описание"
        ])

        self.table.setRowCount(len(self.transactions))

        for row_index, transaction in enumerate(
            self.transactions
        ):
            values = [
                transaction["transaction_date"],
                (
                    "Доход"
                    if transaction["type"] == "income"
                    else "Расход"
                ),
                transaction["category_name"],
                self.format_amount(
                    float(transaction["amount"])
                ),
                transaction["description"] or ""
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                if column_index == 3:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight
                        | Qt.AlignmentFlag.AlignVCenter
                    )

                self.table.setItem(
                    row_index,
                    column_index,
                    item
                )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

    def fill_category_table(self):

        total = sum(
            float(item["total"])
            for item in self.category_data
        )

        self.summary_label.setText(
            f"Общая сумма расходов: "
            f"{self.format_amount(total)}"
        )

        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels([
            "Категория",
            "Сумма расходов"
        ])

        self.table.setRowCount(len(self.category_data))

        for row_index, category in enumerate(
            self.category_data
        ):
            name_item = QTableWidgetItem(
                category["category_name"]
            )

            amount_item = QTableWidgetItem(
                self.format_amount(
                    float(category["total"])
                )
            )

            amount_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )

            self.table.setItem(row_index, 0, name_item)
            self.table.setItem(row_index, 1, amount_item)

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

    def export_to_excel(self):
        """Сохраняет отчёт в Excel."""

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчёт в Excel",
            "FinTrack_Report.xlsx",
            "Excel Files (*.xlsx)"
        )

        if not file_path:
            return

        if not file_path.lower().endswith(".xlsx"):
            file_path += ".xlsx"

        try:
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Отчёт"

            sheet["A1"] = self.report_type
            sheet["A1"].font = Font(
                size=16,
                bold=True
            )

            sheet["A2"] = (
                f"Период: {self.date_from} — {self.date_to}"
            )

            if self.report_type == "Отчёт по категориям":

                sheet.append([])
                sheet.append([
                    "Категория",
                    "Сумма расходов"
                ])

                for category in self.category_data:
                    sheet.append([
                        category["category_name"],
                        float(category["total"])
                    ])

                total = sum(
                    float(item["total"])
                    for item in self.category_data
                )

                sheet.append(["Итого", total])

            else:
                income = sum(
                    float(row["amount"])
                    for row in self.transactions
                    if row["type"] == "income"
                )

                expense = sum(
                    float(row["amount"])
                    for row in self.transactions
                    if row["type"] == "expense"
                )

                sheet.append([])
                sheet.append(["Доходы", income])
                sheet.append(["Расходы", expense])
                sheet.append(["Баланс", income - expense])

                sheet.append([])
                sheet.append([
                    "Дата",
                    "Тип",
                    "Категория",
                    "Сумма",
                    "Описание"
                ])

                for transaction in self.transactions:
                    sheet.append([
                        transaction["transaction_date"],
                        (
                            "Доход"
                            if transaction["type"] == "income"
                            else "Расход"
                        ),
                        transaction["category_name"],
                        float(transaction["amount"]),
                        transaction["description"] or ""
                    ])

            # Оформление заголовков таблицы
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value is not None:
                        cell.alignment = Alignment(
                            vertical="center"
                        )

            # Ширина столбцов
            for column in sheet.columns:
                max_length = 0
                column_letter = column[0].column_letter

                for cell in column:
                    if cell.value is not None:
                        max_length = max(
                            max_length,
                            len(str(cell.value))
                        )

                sheet.column_dimensions[
                    column_letter
                ].width = min(max_length + 4, 45)

            workbook.save(file_path)

            add_report(
                report_type=self.report_type,
                date_from=self.date_from,
                date_to=self.date_to,
                file_format="Excel",
                file_path=file_path
            )

            self.report_exported.emit()

            QMessageBox.information(
                self,
                "Экспорт завершён",
                f"Отчёт сохранён:\n{file_path}"
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка экспорта",
                f"Не удалось сохранить Excel-файл:\n{error}"
            )

    @staticmethod
    def register_pdf_font():
        """Регистрирует шрифт с поддержкой кириллицы."""

        font_paths = [
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\calibri.ttf",
            r"C:\Windows\Fonts\tahoma.ttf"
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(
                    TTFont("FinTrackFont", font_path)
                )
                return "FinTrackFont"

        raise FileNotFoundError(
            "Не найден шрифт с поддержкой кириллицы."
        )

    def export_to_pdf(self):
        """Сохраняет отчёт в PDF."""

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчёт в PDF",
            "FinTrack_Report.pdf",
            "PDF Files (*.pdf)"
        )

        if not file_path:
            return

        if not file_path.lower().endswith(".pdf"):
            file_path += ".pdf"

        try:
            font_name = self.register_pdf_font()

            document = SimpleDocTemplate(
                file_path,
                pagesize=landscape(A4),
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30
            )

            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                "FinTrackTitle",
                parent=styles["Title"],
                fontName=font_name,
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=15
            )

            normal_style = ParagraphStyle(
                "FinTrackNormal",
                parent=styles["Normal"],
                fontName=font_name,
                fontSize=9
            )

            elements = []

            elements.append(
                Paragraph(self.report_type, title_style)
            )

            elements.append(
                Paragraph(
                    f"Период: {self.date_from} — {self.date_to}",
                    normal_style
                )
            )

            elements.append(Spacer(1, 15))

            if self.report_type == "Отчёт по категориям":

                total = sum(
                    float(item["total"])
                    for item in self.category_data
                )

                elements.append(
                    Paragraph(
                        f"Общая сумма расходов: "
                        f"{self.format_amount(total)}",
                        normal_style
                    )
                )

                data = [
                    ["Категория", "Сумма расходов"]
                ]

                for category in self.category_data:
                    data.append([
                        category["category_name"],
                        self.format_amount(
                            float(category["total"])
                        )
                    ])

                col_widths = [350, 200]

            else:
                income = sum(
                    float(row["amount"])
                    for row in self.transactions
                    if row["type"] == "income"
                )

                expense = sum(
                    float(row["amount"])
                    for row in self.transactions
                    if row["type"] == "expense"
                )

                balance = income - expense

                elements.append(
                    Paragraph(
                        f"Доходы: {self.format_amount(income)}"
                        f" | Расходы: {self.format_amount(expense)}"
                        f" | Баланс: {self.format_amount(balance)}",
                        normal_style
                    )
                )

                elements.append(Spacer(1, 15))

                data = [[
                    "Дата",
                    "Тип",
                    "Категория",
                    "Сумма",
                    "Описание"
                ]]

                for transaction in self.transactions:
                    data.append([
                        transaction["transaction_date"],
                        (
                            "Доход"
                            if transaction["type"] == "income"
                            else "Расход"
                        ),
                        transaction["category_name"],
                        self.format_amount(
                            float(transaction["amount"])
                        ),
                        transaction["description"] or ""
                    ])

                col_widths = [85, 65, 140, 100, 320]

            # Преобразуем текст в Paragraph для переноса строк
            formatted_data = []

            for row in data:
                formatted_data.append([
                    Paragraph(str(value), normal_style)
                    for value in row
                ])

            report_table = Table(
                formatted_data,
                colWidths=col_widths,
                repeatRows=1
            )

            report_table.setStyle(
                TableStyle([
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#263B55")
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, -1),
                        font_name
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE"
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [
                            colors.white,
                            colors.HexColor("#F1F5F9")
                        ]
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        7
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        7
                    )
                ])
            )

            elements.append(report_table)

            document.build(elements)

            add_report(
                report_type=self.report_type,
                date_from=self.date_from,
                date_to=self.date_to,
                file_format="PDF",
                file_path=file_path
            )

            self.report_exported.emit()

            QMessageBox.information(
                self,
                "Экспорт завершён",
                f"Отчёт сохранён:\n{file_path}"
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка экспорта",
                f"Не удалось создать PDF-файл:\n{error}"
            )
