
from datetime import date

from database.db import create_connection


def get_period_summary(start_date, end_date):
    """Получает общую сумму доходов и расходов за период."""

    connection = create_connection()

    try:
        result = connection.execute("""
            SELECT
                COALESCE(SUM(
                    CASE
                        WHEN type = 'income' THEN amount
                        ELSE 0
                    END
                ), 0) AS income,

                COALESCE(SUM(
                    CASE
                        WHEN type = 'expense' THEN amount
                        ELSE 0
                    END
                ), 0) AS expense

            FROM transactions

            WHERE transaction_date >= ?
                AND transaction_date <= ?
        """, (
            start_date,
            end_date
        )).fetchone()

        income = float(result["income"])
        expense = float(result["expense"])

        return {
            "income": income,
            "expense": expense,
            "balance": income - expense
        }

    finally:
        connection.close()


def get_expenses_by_category(start_date, end_date):
    """Получает расходы по категориям за период."""

    connection = create_connection()

    try:
        cursor = connection.execute("""
            SELECT
                c.name AS category_name,
                SUM(t.amount) AS total

            FROM transactions AS t

            JOIN categories AS c
                ON t.category_id = c.id

            WHERE t.type = 'expense'
                AND t.transaction_date >= ?
                AND t.transaction_date <= ?

            GROUP BY c.id, c.name

            ORDER BY total DESC
        """, (
            start_date,
            end_date
        ))

        return cursor.fetchall()

    finally:
        connection.close()


def get_monthly_trend(months=6):
    """Получает динамику доходов и расходов по месяцам."""

    today = date.today()

    current_month = date(today.year, today.month, 1)

    month_dates = []

    for i in range(months - 1, -1, -1):
        month_index = current_month.month - i
        year = current_month.year

        while month_index <= 0:
            month_index += 12
            year -= 1

        month_dates.append(date(year, month_index, 1))

    start_date = month_dates[0].isoformat()

    connection = create_connection()

    try:
        cursor = connection.execute("""
            SELECT
                strftime('%Y-%m', transaction_date) AS month,
                type,
                SUM(amount) AS total

            FROM transactions

            WHERE transaction_date >= ?

            GROUP BY month, type

            ORDER BY month
        """, (start_date,))

        results = cursor.fetchall()

        monthly_data = {}

        for month_date in month_dates:
            key = month_date.strftime("%Y-%m")

            monthly_data[key] = {
                "month": month_date.strftime("%m.%Y"),
                "income": 0,
                "expense": 0
            }

        for row in results:
            key = row["month"]

            if key in monthly_data:
                monthly_data[key][row["type"]] = float(
                    row["total"]
                )

        return list(monthly_data.values())

    finally:
        connection.close()
