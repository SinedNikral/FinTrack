
from datetime import date

from database.db import create_connection


def validate_budget_data(amount, month, year):
    """Проверяет корректность параметров бюджета."""

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        raise ValueError("Введите корректную сумму бюджета.")

    if amount < 0:
        raise ValueError("Сумма бюджета не может быть отрицательной.")

    if not isinstance(month, int) or not 1 <= month <= 12:
        raise ValueError("Некорректный месяц.")

    if not isinstance(year, int) or year < 2000:
        raise ValueError("Некорректный год.")

    return amount


def get_budgets(month, year):
    """Получает бюджеты и фактические расходы за месяц."""

    if not isinstance(month, int) or not 1 <= month <= 12:
        raise ValueError("Некорректный месяц.")

    if not isinstance(year, int) or year < 2000:
        raise ValueError("Некорректный год.")

    start_date = date(year, month, 1).isoformat()

    if month == 12:
        end_date = date(year + 1, 1, 1).isoformat()
    else:
        end_date = date(year, month + 1, 1).isoformat()

    connection = create_connection()

    try:
        cursor = connection.execute("""
            SELECT
                b.id,
                b.category_id,
                c.name AS category_name,
                b.amount AS budget_amount,
                b.month,
                b.year,

                COALESCE(SUM(t.amount), 0) AS spent

            FROM budgets AS b

            JOIN categories AS c
                ON b.category_id = c.id

            LEFT JOIN transactions AS t
                ON t.category_id = b.category_id
                AND t.type = 'expense'
                AND t.transaction_date >= ?
                AND t.transaction_date < ?

            WHERE b.month = ?
                AND b.year = ?

            GROUP BY
                b.id,
                b.category_id,
                c.name,
                b.amount,
                b.month,
                b.year

            ORDER BY c.name
        """, (
            start_date,
            end_date,
            month,
            year
        ))

        return cursor.fetchall()

    finally:
        connection.close()


def add_budget(category_id, amount, month, year):
    """Добавляет бюджет для категории расходов."""

    amount = validate_budget_data(amount, month, year)

    connection = create_connection()

    try:
        category = connection.execute("""
            SELECT type
            FROM categories
            WHERE id = ?
        """, (category_id,)).fetchone()

        if category is None:
            raise ValueError("Выбранная категория не найдена.")

        if category["type"] != "expense":
            raise ValueError(
                "Бюджет можно установить только для категории расходов."
            )

        connection.execute("""
            INSERT INTO budgets (
                category_id,
                amount,
                month,
                year
            )
            VALUES (?, ?, ?, ?)
        """, (
            category_id,
            amount,
            month,
            year
        ))

        connection.commit()

    finally:
        connection.close()


def update_budget(budget_id, amount):
    """Изменяет сумму существующего бюджета."""

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        raise ValueError("Введите корректную сумму бюджета.")

    if amount < 0:
        raise ValueError("Сумма бюджета не может быть отрицательной.")

    connection = create_connection()

    try:
        cursor = connection.execute("""
            UPDATE budgets
            SET amount = ?
            WHERE id = ?
        """, (
            amount,
            budget_id
        ))

        if cursor.rowcount == 0:
            raise ValueError("Бюджет не найден.")

        connection.commit()

    finally:
        connection.close()


def delete_budget(budget_id):
    """Удаляет бюджет."""

    connection = create_connection()

    try:
        cursor = connection.execute("""
            DELETE FROM budgets
            WHERE id = ?
        """, (budget_id,))

        if cursor.rowcount == 0:
            raise ValueError("Бюджет не найден.")

        connection.commit()

    finally:
        connection.close()
