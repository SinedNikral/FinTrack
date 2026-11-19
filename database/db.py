import sqlite3
import sys
from pathlib import Path


# Определяем путь к базе данных
if getattr(sys, "frozen", False):
    DATABASE_PATH = (
        Path(sys.executable).resolve().parent / "fintrack.db"
    )
else:
    DATABASE_PATH = (
        Path(__file__).resolve().parent.parent / "fintrack.db"
    )


def create_connection():
    """Создаёт подключение к базе данных."""

    connection = sqlite3.connect(DATABASE_PATH)

    # Позволяет обращаться к столбцам по названиям
    connection.row_factory = sqlite3.Row

    # Включаем контроль внешних ключей
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def init_database():
    """Создаёт таблицы и начальные категории."""

    with create_connection() as connection:

        # Таблица категорий
        connection.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL
                    CHECK(type IN ('income', 'expense')),
                is_default INTEGER NOT NULL DEFAULT 0,
                UNIQUE(name, type)
            )
        """)

        # Таблица финансовых операций
        connection.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL
                    CHECK(type IN ('income', 'expense')),
                amount REAL NOT NULL CHECK(amount > 0),
                category_id INTEGER NOT NULL,
                transaction_date TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (category_id)
                    REFERENCES categories(id)
                    ON DELETE RESTRICT
            )
        """)

        # Таблица месячных бюджетов
        connection.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK(amount >= 0),
                month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
                year INTEGER NOT NULL CHECK(year >= 2000),

                FOREIGN KEY (category_id)
                    REFERENCES categories(id)
                    ON DELETE RESTRICT,

                UNIQUE(category_id, month, year)
            )
        """)

        # Таблица настроек приложения
        connection.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL
            )
        """)

        # Таблица истории сформированных отчётов
        connection.execute("""
            CREATE TABLE IF NOT EXISTS report_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                date_from TEXT NOT NULL,
                date_to TEXT NOT NULL,
                file_format TEXT NOT NULL
                    CHECK(file_format IN ('PDF', 'Excel')),
                file_path TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Индексы для ускорения поиска операций
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_date
            ON transactions(transaction_date)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_category
            ON transactions(category_id)
        """)

        # Стандартные категории доходов
        income_categories = [
            "Зарплата",
            "Подарки",
            "Дополнительный доход",
            "Прочие доходы"
        ]

        # Стандартные категории расходов
        expense_categories = [
            "Продукты",
            "Транспорт",
            "Жильё",
            "Здоровье",
            "Развлечения",
            "Покупки",
            "Образование",
            "Прочие расходы"
        ]

        for name in income_categories:
            connection.execute("""
                INSERT OR IGNORE INTO categories (name, type, is_default)
                VALUES (?, 'income', 1)
            """, (name,))

        for name in expense_categories:
            connection.execute("""
                INSERT OR IGNORE INTO categories (name, type, is_default)
                VALUES (?, 'expense', 1)
            """, (name,))

    print("База данных успешно инициализирована.")
