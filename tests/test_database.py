"""
Database Configuration and Schema Verification Tests.
"""
import json
from pathlib import Path
import pytest
from config import Config


def test_config_defaults():
    assert Config.MYSQL_HOST is not None
    assert Config.MYSQL_PORT > 0
    assert Config.MYSQL_DATABASE == "kannada_everyone"
    assert Config.DEFAULT_TIMEZONE == "Asia/Kolkata"


def test_schema_file_exists_and_valid():
    schema_path = Path(__file__).resolve().parent.parent / "schema.sql"
    assert schema_path.exists()
    content = schema_path.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS `users`" in content
    assert "CREATE TABLE IF NOT EXISTS `situations`" in content
    assert "CREATE TABLE IF NOT EXISTS `lessons`" in content
    assert "CREATE TABLE IF NOT EXISTS `vocabulary`" in content
    assert "utf8mb4" in content


def test_seed_situations_json_valid():
    sit_path = Path(__file__).resolve().parent.parent / "data" / "situations.json"
    assert sit_path.exists()
    with open(sit_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) >= 9
    slugs = [s["slug"] for s in data]
    assert len(slugs) == len(set(slugs))  # Uniqueness
    for s in data:
        assert "title" in s
        assert "description" in s
        assert "category" in s
        assert "ai_role" in s


def test_seed_lessons_json_valid():
    les_path = Path(__file__).resolve().parent.parent / "data" / "seed_lessons.json"
    assert les_path.exists()
    with open(les_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) >= 5
    for l in data:
        assert "slug" in l
        assert "level" in l
        assert "content_json" in l
        content = l["content_json"]
        assert "exercises" in content
        assert len(content["exercises"]) > 0


def test_seed_vocabulary_json_valid():
    vocab_path = Path(__file__).resolve().parent.parent / "data" / "seed_vocabulary.json"
    assert vocab_path.exists()
    with open(vocab_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) >= 20
    for v in data:
        assert "kannada_text" in v
        assert "transliteration" in v
        assert "english_meaning" in v
        assert "hindi_meaning" in v
        assert "marathi_meaning" in v
