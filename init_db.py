"""
Database Initialization and Seed Data Loader.
Executes schema.sql and populates situations, lessons, and vocabulary idempotently.
"""
import json
import logging
import os
from pathlib import Path
import mysql.connector
from config import Config
from db import get_connection, get_db_cursor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("init_db")


def create_database_if_not_exists():
    """Connects to MySQL server without selecting DB and creates the database if missing."""
    logger.info("Verifying database '%s' existence on %s:%s...", Config.MYSQL_DATABASE, Config.MYSQL_HOST, Config.MYSQL_PORT)
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci"
        )
        cursor = conn.cursor()
        create_sql = f"""
        CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DATABASE}`
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci;
        """
        cursor.execute(create_sql)
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Database '%s' is verified and ready.", Config.MYSQL_DATABASE)
    except Exception as e:
        logger.error("Could not verify or create database: %s", str(e))
        raise


def apply_schema(schema_path: Path):
    """Executes schema.sql against the target database."""
    logger.info("Applying schema from %s...", schema_path)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split statements by semicolon while ignoring comments
    statements = []
    current_stmt = []
    for line in sql_content.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("--"):
            continue
        current_stmt.append(line)
        if trimmed.endswith(";"):
            stmt_text = "\n".join(current_stmt).strip()
            if stmt_text:
                statements.append(stmt_text)
            current_stmt = []

    conn = get_connection()
    cursor = conn.cursor()
    try:
        for stmt in statements:
            if not stmt:
                continue
            cursor.execute(stmt)
        conn.commit()
        logger.info("Schema applied successfully (%d statements executed).", len(statements))
    except Exception as e:
        conn.rollback()
        logger.error("Error executing schema statement: %s", str(e))
        raise
    finally:
        cursor.close()
        conn.close()


def seed_situations(data_path: Path):
    """Seeds situations idempotently from data/situations.json."""
    if not data_path.exists():
        logger.warning("Situations file not found at %s. Skipping.", data_path)
        return

    with open(data_path, "r", encoding="utf-8") as f:
        situations = json.load(f)

    logger.info("Seeding %d situations...", len(situations))
    query = """
    INSERT INTO `situations` (`slug`, `title`, `description`, `category`, `difficulty_level`, `ai_role`, `system_hint`, `is_active`)
    VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
    ON DUPLICATE KEY UPDATE
      `title` = VALUES(`title`),
      `description` = VALUES(`description`),
      `category` = VALUES(`category`),
      `difficulty_level` = VALUES(`difficulty_level`),
      `ai_role` = VALUES(`ai_role`),
      `system_hint` = VALUES(`system_hint`);
    """
    with get_db_cursor(commit=True) as (_, cursor):
        for sit in situations:
            cursor.execute(query, (
                sit["slug"],
                sit["title"],
                sit["description"],
                sit["category"],
                sit.get("difficulty_level", 1),
                sit["ai_role"],
                sit.get("system_hint", "")
            ))
    logger.info("Situations seeded successfully.")


def seed_lessons(data_path: Path):
    """Seeds structured lessons idempotently from data/seed_lessons.json."""
    if not data_path.exists():
        logger.warning("Lessons file not found at %s. Skipping.", data_path)
        return

    with open(data_path, "r", encoding="utf-8") as f:
        lessons = json.load(f)

    logger.info("Seeding %d lessons...", len(lessons))
    query = """
    INSERT INTO `lessons` (`slug`, `title`, `description`, `level`, `lesson_order`, `estimated_minutes`, `content_json`, `pass_score`, `is_active`)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
    ON DUPLICATE KEY UPDATE
      `title` = VALUES(`title`),
      `description` = VALUES(`description`),
      `level` = VALUES(`level`),
      `lesson_order` = VALUES(`lesson_order`),
      `estimated_minutes` = VALUES(`estimated_minutes`),
      `content_json` = VALUES(`content_json`),
      `pass_score` = VALUES(`pass_score`);
    """
    with get_db_cursor(commit=True) as (_, cursor):
        for les in lessons:
            content_str = json.dumps(les["content_json"], ensure_ascii=False)
            cursor.execute(query, (
                les["slug"],
                les["title"],
                les["description"],
                les["level"],
                les["lesson_order"],
                les.get("estimated_minutes", 10),
                content_str,
                les.get("pass_score", 70)
            ))
    logger.info("Lessons seeded successfully.")


def seed_vocabulary(data_path: Path):
    """Seeds vocabulary library idempotently from data/seed_vocabulary.json."""
    if not data_path.exists():
        logger.warning("Vocabulary file not found at %s. Skipping.", data_path)
        return

    with open(data_path, "r", encoding="utf-8") as f:
        vocab_list = json.load(f)

    logger.info("Seeding %d vocabulary items...", len(vocab_list))
    query = """
    INSERT INTO `vocabulary` (
      `kannada_text`, `transliteration`, `english_meaning`, `hindi_meaning`, `marathi_meaning`,
      `example_kannada`, `example_transliteration`, `example_translation_json`,
      `category`, `level`, `audio_reference`
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
      `transliteration` = VALUES(`transliteration`),
      `english_meaning` = VALUES(`english_meaning`),
      `hindi_meaning` = VALUES(`hindi_meaning`),
      `marathi_meaning` = VALUES(`marathi_meaning`),
      `example_kannada` = VALUES(`example_kannada`),
      `example_transliteration` = VALUES(`example_transliteration`),
      `example_translation_json` = VALUES(`example_translation_json`),
      `level` = VALUES(`level`),
      `audio_reference` = VALUES(`audio_reference`);
    """
    with get_db_cursor(commit=True) as (_, cursor):
        for item in vocab_list:
            ex_trans_str = json.dumps(item.get("example_translation", {}), ensure_ascii=False)
            cursor.execute(query, (
                item["kannada_text"],
                item["transliteration"],
                item["english_meaning"],
                item["hindi_meaning"],
                item["marathi_meaning"],
                item.get("example_kannada", ""),
                item.get("example_transliteration", ""),
                ex_trans_str,
                item["category"],
                item.get("level", 1),
                item.get("audio_reference")
            ))
    logger.info("Vocabulary seeded successfully.")


def initialize_all():
    """Coordinates full idempotent database initialization."""
    base_dir = Path(__file__).resolve().parent
    schema_file = base_dir / "schema.sql"
    situations_file = base_dir / "data" / "situations.json"
    lessons_file = base_dir / "data" / "seed_lessons.json"
    vocab_file = base_dir / "data" / "seed_vocabulary.json"

    logger.info("=== Starting Database Initialization for Kannada for Everyone ===")
    create_database_if_not_exists()
    apply_schema(schema_file)
    seed_situations(situations_file)
    seed_lessons(lessons_file)
    seed_vocabulary(vocab_file)
    logger.info("=== Database Initialization Completed Successfully! ===")


if __name__ == "__main__":
    try:
        initialize_all()
    except Exception as e:
        logger.error("Initialization failed: %s", str(e))
        exit(1)
