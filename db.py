"""
Database Connection and Transaction Management for MySQL.
Provides safe connection handling, utf8mb4 collation, and transaction management.
"""
from contextlib import contextmanager
import logging
import mysql.connector
from mysql.connector import Error as MySQLError
from config import Config

logger = logging.getLogger("kfe_db")


def get_connection(database: str | None = None) -> mysql.connector.MySQLConnection:
    """
    Creates and returns a new MySQL database connection configured with utf8mb4.
    If database is None, defaults to Config.MYSQL_DATABASE.
    """
    db_name = "kannada_everyone" if database is None else database
    kwargs = {
        "host": "127.0.0.1",
        "port": "3306",
        "user": "root",
        "password": "root",
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "autocommit": False
    }
    if db_name:
        kwargs["database"] = db_name

    try:
        conn = mysql.connector.connect(**kwargs)
        return conn
    except MySQLError as e:
        logger.error("Failed to connect to MySQL: %s", str(e))
        raise ConnectionError(f"Database connection failed: {e.msg if hasattr(e, 'msg') else str(e)}")


@contextmanager
def get_db_cursor(commit: bool = False, dictionary: bool = True):
    """
    Context manager yielding a (connection, cursor) tuple.
    Automatically commits if commit=True and rolls back upon exception.
    Always closes both cursor and connection cleanly.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=dictionary)
        yield conn, cursor
        if commit:
            conn.commit()
    except Exception as e:
        if conn and conn.is_connected():
            try:
                conn.rollback()
            except Exception:
                pass
        raise e
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn and conn.is_connected():
            try:
                conn.close()
            except Exception:
                pass


def check_database_connection() -> tuple[bool, str]:
    """
    Tests database connectivity and returns (is_healthy, status_message).
    """
    try:
        with get_db_cursor(commit=False, dictionary=True) as (_, cursor):
            cursor.execute("SELECT 1 AS alive, VERSION() AS version;")
            row = cursor.fetchone()
            if row and row.get("alive") == 1:
                return True, f"Connected to MySQL {row.get('version', '')}"
            return False, "Database responded with unexpected result."
    except Exception as e:
        return False, str(e)
