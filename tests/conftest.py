import pytest
import asyncio
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для асинхронных тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Настройка тестового окружения"""
    # Устанавливаем переменные окружения для тестов
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = "sqlite:///test.db"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"

    yield

    # Очистка после тестов
    test_db_path = "test.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
