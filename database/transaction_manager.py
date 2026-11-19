from datetime import date

from database.db import create_connection


def get_transactions(
    transaction_type=None,
    category_id=None,
    date_from=None,
    date_to=None
):
    """Получает финансовые операции с возможностью фильтрации."""

    query = """
        SELECT
            t.id,
            t.type,
            t.amount,
            t.category_id,
            c.name AS category_name,
            t.transaction_date,
            t.description
        FROM transactions AS t
        JOIN categories AS c ON t.category_id = c.id
        WHERE 1 = 1
    """

    params = []

    if transaction_type:
        if transaction_type not in ("income", "expense"):
            raise ValueError("Неизвестный тип операции.")

        query += " AND t.type = ?"
        params.append(transaction_type)

    if category_id is not None:
        query += " AND t.category_id = ?"
        params.append(category_id)

    if date_from:
        query += " AND t.transaction_date >= ?"
        params.append(date_from)

    if date_to:
        query += " AND t.transaction_date <= ?"
        params.append(date_to)

    query += " ORDER BY t.transaction_date DESC, t.id DESC"

    connection = create_connection()

    try:
        cursor = connection.execute(query, params)
        return cursor.fetchall()
    finally:
        connection.close()


def add_transaction(
    transaction_type,
    amount,
    category_id,
    transaction_date,
    description=""
):
    """Добавляет новую финансовую операцию."""

    if transaction_type not in ("income", "expense"):
        raise ValueError("Необходимо выбрать тип операции.")

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        raise ValueError("Введите корректную сумму.")

    if amount <= 0:
        raise ValueError("Сумма должна быть больше нуля.")

    if not date_is_valid(transaction_date):
        raise ValueError("Некорректная дата операции.")

    description = description.strip()

    connection = create_connection()

    try:
        category = connection.execute("""
            SELECT type
            FROM categories
            WHERE id = ?
        """, (category_id,)).fetchone()

        if category is None:
            raise ValueError("Выбранная категория не найдена.")

        if category["type"] != transaction_type:
            raise ValueError(
                "Тип категории не соответствует типу операции."
            )

        connection.execute("""
            INSERT INTO transactions (
                type,
                amount,
                category_id,
                transaction_date,
                description
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            transaction_type,
            amount,
            category_id,
            transaction_date,
            description
        ))

        connection.commit()

    finally:
        connection.close()


def update_transaction(
    transaction_id,
    transaction_type,
    amount,
    category_id,
    transaction_date,
    description=""
):
    """Изменяет существующую финансовую операцию."""

    if transaction_type not in ("income", "expense"):
        raise ValueError("Необходимо выбрать тип операции.")

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        raise ValueError("Введите корректную сумму.")

    if amount <= 0:
        raise ValueError("Сумма должна быть больше нуля.")

    if not date_is_valid(transaction_date):
        raise ValueError("Некорректная дата операции.")

    connection = create_connection()

    try:
        category = connection.execute("""
            SELECT type
            FROM categories
            WHERE id = ?
        """, (category_id,)).fetchone()

        if category is None:
            raise ValueError("Выбранная категория не найдена.")

        if category["type"] != transaction_type:
            raise ValueError(
                "Тип категории не соответствует типу операции."
            )

        cursor = connection.execute("""
            UPDATE transactions
            SET
                type = ?,
                amount = ?,
                category_id = ?,
                transaction_date = ?,
                description = ?
            WHERE id = ?
        """, (
            transaction_type,
            amount,
            category_id,
            transaction_date,
            description.strip(),
            transaction_id
        ))

        if cursor.rowcount == 0:
            raise ValueError("Операция не найдена.")

        connection.commit()

    finally:
        connection.close()


def delete_transaction(transaction_id):
    """Удаляет финансовую операцию."""

    connection = create_connection()

    try:
        cursor = connection.execute("""
            DELETE FROM transactions
            WHERE id = ?
        """, (transaction_id,))

        if cursor.rowcount == 0:
            raise ValueError("Операция не найдена.")

        connection.commit()

    finally:
        connection.close()


def date_is_valid(value):
    """Проверяет дату в формате YYYY-MM-DD."""

    try:
        date.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False


def get_transaction_summary():
    """Возвращает общую статистику финансовых операций."""

    connection = create_connection()

    try:
        result = connection.execute("""
            SELECT
                COALESCE(
                    SUM(CASE WHEN type = 'income'
                        THEN amount ELSE 0 END),
                    0
                ) AS total_income,

                COALESCE(
                    SUM(CASE WHEN type = 'expense'
                        THEN amount ELSE 0 END),
                    0
                ) AS total_expense

            FROM transactions
        """).fetchone()

        total_income = result["total_income"]
        total_expense = result["total_expense"]

        return {
            "income": total_income,
            "expense": total_expense,
            "balance": total_income - total_expense
        }

    finally:
        connection.close()


def get_recent_transactions(limit=5):
    """Возвращает последние финансовые операции."""

    connection = create_connection()

    try:
        cursor = connection.execute("""
            SELECT
                t.id,
                t.type,
                t.amount,
                t.transaction_date,
                t.description,
                c.name AS category_name

            FROM transactions AS t

            JOIN categories AS c
                ON t.category_id = c.id

            ORDER BY
                t.transaction_date DESC,
                t.id DESC

            LIMIT ?
        """, (limit,))

        return cursor.fetchall()

    finally:
        connection.close()
