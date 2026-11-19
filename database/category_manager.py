
import sqlite3

from database.db import create_connection


def get_categories(category_type=None):
    """
    Возвращает список категорий.

    category_type:
        'income'  — доходы
        'expense' — расходы
        None      — все категории
    """

    connection = create_connection()

    try:
        if category_type is None:
            cursor = connection.execute("""
                SELECT id, name, type, is_default
                FROM categories
                ORDER BY type, name
            """)
        else:
            if category_type not in ("income", "expense"):
                raise ValueError("Неизвестный тип категории.")

            cursor = connection.execute("""
                SELECT id, name, type, is_default
                FROM categories
                WHERE type = ?
                ORDER BY name
            """, (category_type,))

        return cursor.fetchall()

    finally:
        connection.close()


def add_category(name, category_type):
    """Добавляет новую категорию."""

    name = name.strip()

    if not name:
        raise ValueError("Название категории не может быть пустым.")

    if category_type not in ("income", "expense"):
        raise ValueError("Необходимо выбрать тип категории.")

    connection = create_connection()

    try:
        connection.execute("""
            INSERT INTO categories (name, type, is_default)
            VALUES (?, ?, 0)
        """, (name, category_type))

        connection.commit()

    except sqlite3.IntegrityError:
        connection.rollback()
        raise ValueError(
            "Категория с таким названием уже существует "
            "в выбранном типе."
        )

    finally:
        connection.close()


def update_category(category_id, new_name):
    """Изменяет название существующей категории."""

    new_name = new_name.strip()

    if not new_name:
        raise ValueError("Название категории не может быть пустым.")

    connection = create_connection()

    try:
        cursor = connection.execute("""
            UPDATE categories
            SET name = ?
            WHERE id = ?
        """, (new_name, category_id))

        if cursor.rowcount == 0:
            raise ValueError("Категория не найдена.")

        connection.commit()

    except sqlite3.IntegrityError:
        connection.rollback()
        raise ValueError(
            "Категория с таким названием уже существует."
        )

    finally:
        connection.close()


def delete_category(category_id):
    """Удаляет категорию, если она нигде не используется."""

    connection = create_connection()

    try:
        cursor = connection.execute("""
            DELETE FROM categories
            WHERE id = ?
        """, (category_id,))

        if cursor.rowcount == 0:
            raise ValueError("Категория не найдена.")

        connection.commit()

    except sqlite3.IntegrityError:
        connection.rollback()
        raise ValueError(
            "Нельзя удалить категорию, которая используется "
            "в операциях или бюджетах."
        )

    finally:
        connection.close()
