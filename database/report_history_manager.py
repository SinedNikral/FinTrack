
from database.db import create_connection


def add_report(
    report_type,
    date_from,
    date_to,
    file_format,
    file_path
):
    """Добавляет успешно сформированный отчёт в историю."""

    with create_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO report_history (
                report_type,
                date_from,
                date_to,
                file_format,
                file_path
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            report_type,
            date_from,
            date_to,
            file_format,
            str(file_path)
        ))

        return cursor.lastrowid


def get_reports():
    """Возвращает историю отчётов."""

    with create_connection() as connection:
        cursor = connection.execute("""
            SELECT *
            FROM report_history
            ORDER BY created_at DESC, id DESC
        """)

        return cursor.fetchall()


def delete_report(report_id):
    """Удаляет запись из истории."""

    with create_connection() as connection:
        connection.execute("""
            DELETE FROM report_history
            WHERE id = ?
        """, (report_id,))
