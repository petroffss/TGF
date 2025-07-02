import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import Base, get_db

# Тестовая база данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Переопределение зависимости базы данных для тестов
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

class TestAPI:
    """Тесты основного API"""

    def test_read_root(self, setup_database):
        """Тест корневого эндпоинта"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

    def test_health_check(self, setup_database):
        """Тест health check эндпоинта"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_get_channels_empty(self, setup_database):
        """Тест получения каналов (пустой список)"""
        response = client.get("/channels")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_channels_with_search(self, setup_database):
        """Тест поиска каналов"""
        response = client.get("/channels?search=test")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_channels_with_filters(self, setup_database):
        """Тест фильтрации каналов"""
        response = client.get("/channels?theme=Tech&min_subscribers=1000")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_nonexistent_channel(self, setup_database):
        """Тест получения несуществующего канала"""
        response = client.get("/channels/999999")
        assert response.status_code == 404

    def test_get_overview_stats(self, setup_database):
        """Тест получения статистики"""
        response = client.get("/stats/overview")
        assert response.status_code == 200
        stats = response.json()
        assert "total_channels" in stats
        assert "total_connections" in stats

class TestChannelAnalysis:
    """Тесты анализа каналов"""

    def test_analyze_nonexistent_channel(self, setup_database):
        """Тест анализа несуществующего канала"""
        response = client.post("/channels/999999/analyze", json={
            "analysis_types": ["content", "temporal", "network"],
            "depth": 2
        })
        assert response.status_code == 404

    def test_get_analysis_results_not_found(self, setup_database):
        """Тест получения несуществующих результатов анализа"""
        response = client.get("/analysis/999999")
        assert response.status_code == 404

class TestConnections:
    """Тесты связей между каналами"""

    def test_get_connections_empty(self, setup_database):
        """Тест получения связей (пустой список)"""
        response = client.get("/connections")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_connections_with_filters(self, setup_database):
        """Тест фильтрации связей"""
        response = client.get("/connections?source_id=1&connection_type=content_similarity")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

@pytest.mark.asyncio
class TestAsyncAPI:
    """Асинхронные тесты API"""

    async def test_async_client(self):
        """Тест асинхронного клиента"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/")
            assert response.status_code == 200
