# tests/test_api.py - Тесты для API
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

# tests/test_content_analyzer.py - Тесты анализатора контента
import pytest
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis_engine import ContentAnalyzer, AnalysisConfig

class TestContentAnalyzer:
    """Тесты анализатора контента"""
    
    @pytest.fixture
    def analyzer(self):
        config = AnalysisConfig()
        return ContentAnalyzer(config)
    
    @pytest.fixture
    def sample_posts(self):
        return [
            {
                'id': 1,
                'text': 'Это тестовый пост о технологиях и искусственном интеллекте',
                'published_at': datetime.now()
            },
            {
                'id': 2,
                'text': 'Это тестовый пост о технологиях и машинном обучении',
                'published_at': datetime.now()
            },
            {
                'id': 3,
                'text': 'Совершенно другая тема - спорт и футбол',
                'published_at': datetime.now()
            }
        ]
    
    def test_text_similarity_identical(self, analyzer):
        """Тест схожести идентичных текстов"""
        text = "Это тестовый текст"
        similarity = analyzer.calculate_text_similarity(text, text)
        assert similarity['overall'] == 1.0
    
    def test_text_similarity_different(self, analyzer):
        """Тест схожести разных текстов"""
        text1 = "Технологии и искусственный интеллект"
        text2 = "Спорт и футбол"
        similarity = analyzer.calculate_text_similarity(text1, text2)
        assert similarity['overall'] < 0.5
    
    def test_text_similarity_similar(self, analyzer):
        """Тест схожести похожих текстов"""
        text1 = "Искусственный интеллект и машинное обучение"
        text2 = "Машинное обучение и искусственный интеллект"
        similarity = analyzer.calculate_text_similarity(text1, text2)
        assert similarity['overall'] > 0.7
    
    def test_clean_text(self, analyzer):
        """Тест очистки текста"""
        dirty_text = "Привет @username #hashtag http://example.com !!!"
        clean_text = analyzer._clean_text(dirty_text)
        assert "@username" not in clean_text
        assert "#hashtag" not in clean_text
        assert "http://example.com" not in clean_text
    
    def test_detect_duplicates(self, analyzer, sample_posts):
        """Тест обнаружения дубликатов"""
        duplicates = analyzer.detect_duplicates(sample_posts)
        assert isinstance(duplicates, list)
        # Первые два поста должны быть похожими
        if duplicates:
            assert any(d['similarity_metrics']['overall'] > 0.5 for d in duplicates)
    
    def test_extract_topics_empty(self, analyzer):
        """Тест извлечения тем из пустого списка"""
        result = analyzer.extract_topics([])
        assert result['topics'] == []
        assert result['topic_distribution'] == []
    
    def test_extract_topics_valid(self, analyzer):
        """Тест извлечения тем из валидных текстов"""
        texts = [
            "Технологии искусственного интеллекта развиваются быстро",
            "Машинное обучение используется в различных областях",
            "Спорт и здоровье важны для каждого человека",
            "Футбол - популярная игра во всем мире"
        ]
        result = analyzer.extract_topics(texts, n_topics=2)
        assert len(result['topics']) <= 2
        assert len(result['topic_distribution']) == len(texts)

# tests/test_temporal_analyzer.py - Тесты временного анализатора
import pytest
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis_engine import TemporalAnalyzer, AnalysisConfig

class TestTemporalAnalyzer:
    """Тесты временного анализатора"""
    
    @pytest.fixture
    def analyzer(self):
        config = AnalysisConfig()
        return TemporalAnalyzer(config)
    
    @pytest.fixture
    def sample_posts_channel1(self):
        base_time = datetime(2023, 12, 1, 10, 0, 0)
        return [
            {
                'id': 1,
                'published_at': base_time,
                'text': 'Post 1'
            },
            {
                'id': 2,
                'published_at': base_time + timedelta(hours=1),
                'text': 'Post 2'
            },
            {
                'id': 3,
                'published_at': base_time + timedelta(hours=2),
                'text': 'Post 3'
            }
        ]
    
    @pytest.fixture
    def sample_posts_channel2(self):
        base_time = datetime(2023, 12, 1, 10, 5, 0)  # 5 минут разница
        return [
            {
                'id': 4,
                'published_at': base_time,
                'text': 'Post 4'
            },
            {
                'id': 5,
                'published_at': base_time + timedelta(hours=1),
                'text': 'Post 5'
            },
            {
                'id': 6,
                'published_at': base_time + timedelta(hours=2),
                'text': 'Post 6'
            }
        ]
    
    def test_get_hourly_activity(self, analyzer, sample_posts_channel1):
        """Тест получения почасовой активности"""
        activity = analyzer._get_hourly_activity(sample_posts_channel1)
        assert isinstance(activity, dict)
        assert activity[10] == 1  # 10:00 - один пост
        assert activity[11] == 1  # 11:00 - один пост
        assert activity[12] == 1  # 12:00 - один пост
    
    def test_find_synchronized_posts(self, analyzer, sample_posts_channel1, sample_posts_channel2):
        """Тест поиска синхронных постов"""
        sync_posts = analyzer._find_synchronized_posts(sample_posts_channel1, sample_posts_channel2)
        assert isinstance(sync_posts, list)
        # Все посты должны быть синхронными (разница 5 минут)
        assert len(sync_posts) == 3
        for sync in sync_posts:
            assert sync['time_diff_minutes'] == 5.0
    
    def test_calculate_time_correlation(self, analyzer, sample_posts_channel1, sample_posts_channel2):
        """Тест вычисления временной корреляции"""
        correlation = analyzer.calculate_time_correlation(sample_posts_channel1, sample_posts_channel2)
        
        assert isinstance(correlation, dict)
        assert 'hourly_correlation' in correlation
        assert 'synchronized_posts' in correlation
        assert 'sequence_analysis' in correlation
        
        # Корреляция должна быть высокой (одинаковые паттерны)
        assert correlation['hourly_correlation'] > 0.8
        assert correlation['synchronized_posts'] == 3
    
    def test_find_peak_hours(self, analyzer):
        """Тест поиска часов пиковой активности"""
        hourly_activity = {10: 5, 11: 3, 12: 8, 13: 2, 14: 6}
        peak_hours = analyzer._find_peak_hours(hourly_activity, top_k=3)
        
        assert peak_hours == [12, 10, 14]  # Сортировка по убыванию активности

# tests/test_network_analyzer.py - Тесты сетевого анализатора
import pytest
import networkx as nx
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis_engine import NetworkAnalyzer, AnalysisConfig

class TestNetworkAnalyzer:
    """Тесты сетевого анализатора"""
    
    @pytest.fixture
    def analyzer(self):
        config = AnalysisConfig()
        return NetworkAnalyzer(config)
    
    @pytest.fixture
    def sample_connections(self):
        return [
            {
                'source_id': 1,
                'target_id': 2,
                'strength': 0.8,
                'connection_type': 'content_similarity'
            },
            {
                'source_id': 2,
                'target_id': 3,
                'strength': 0.6,
                'connection_type': 'time_correlation'
            },
            {
                'source_id': 1,
                'target_id': 3,
                'strength': 0.9,
                'connection_type': 'admin_overlap'
            }
        ]
    
    def test_build_channel_network(self, analyzer, sample_connections):
        """Тест построения сети каналов"""
        graph = analyzer.build_channel_network(sample_connections)
        
        assert isinstance(graph, nx.Graph)
        assert graph.number_of_nodes() == 3
        assert graph.number_of_edges() == 3
        
        # Проверяем атрибуты рёбер
        edge_data = graph.get_edge_data(1, 2)
        assert edge_data['weight'] == 0.8
        assert edge_data['connection_type'] == 'content_similarity'
    
    def test_calculate_network_metrics(self, analyzer, sample_connections):
        """Тест вычисления сетевых метрик"""
        graph = analyzer.build_channel_network(sample_connections)
        metrics = analyzer.calculate_network_metrics(graph, 1)
        
        assert isinstance(metrics, dict)
        assert 'degree' in metrics
        assert 'degree_centrality' in metrics
        assert 'pagerank' in metrics
        assert 'clustering_coefficient' in metrics
        
        # Узел 1 связан с узлами 2 и 3
        assert metrics['degree'] == 2
        assert metrics['neighbors_count'] == 2
    
    def test_empty_network_metrics(self, analyzer):
        """Тест метрик для пустой сети"""
        empty_graph = nx.Graph()
        metrics = analyzer.calculate_network_metrics(empty_graph, 1)
        
        # Должны быть нулевые метрики
        assert metrics['degree'] == 0
        assert metrics['degree_centrality'] == 0.0
        assert metrics['neighbors_count'] == 0
    
    def test_detect_communities(self, analyzer, sample_connections):
        """Тест обнаружения сообществ"""
        graph = analyzer.build_channel_network(sample_connections)
        communities = analyzer.detect_communities(graph)
        
        assert isinstance(communities, dict)
        assert 'communities' in communities
        assert 'modularity' in communities
        assert 'community_count' in communities
        
        # В небольшой плотно связанной сети может быть одно сообщество
        assert communities['community_count'] >= 1

# tests/conftest.py - Конфигурация pytest
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

# pytest.ini - Конфигурация pytest
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=.
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests

---

# API_DOCUMENTATION.md - Документация API
# API Документация - Система анализа Telegram каналов

## Обзор

API системы анализа Telegram каналов предоставляет интерфейс для управления каналами, анализа их взаимосвязей и получения аналитических данных.

**Base URL:** `http://localhost:8000`  
**Версия API:** 1.0.0

## Аутентификация

```http
Authorization: Bearer <jwt_token>
```

## Эндпоинты

### Общие

#### GET /
Корневой эндпоинт API

**Ответ:**
```json
{
  "message": "Telegram Channels Analysis API",
  "version": "1.0.0"
}
```

#### GET /health
Проверка состояния API

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2023-12-01T12:00:00Z",
  "database": "connected",
  "redis": "connected"
}
```

### Каналы

#### GET /channels
Получение списка каналов с фильтрацией

**Параметры запроса:**
- `search` (string, optional) - Поиск по названию или username
- `theme` (string, optional) - Фильтр по тематике
- `min_subscribers` (integer, optional) - Минимальное количество подписчиков
- `limit` (integer, optional, default: 50) - Количество результатов

**Пример запроса:**
```http
GET /channels?search=tech&min_subscribers=1000&limit=20
```

**Ответ:**
```json
[
  {
    "id": 1,
    "name": "Tech Channel",
    "username": "@tech_channel",
    "description": "Канал о технологиях",
    "subscribers_count": 15000,
    "theme": "Технологии",
    "verified": true,
    "created_at": "2023-01-15T10:30:00Z",
    "last_post_date": "2023-12-01T08:45:00Z"
  }
]
```

#### GET /channels/{channel_id}
Получение информации о конкретном канале

**Параметры пути:**
- `channel_id` (integer) - ID канала

**Ответ:**
```json
{
  "id": 1,
  "name": "Tech Channel",
  "username": "@tech_channel",
  "description": "Канал о технологиях",
  "subscribers_count": 15000,
  "posts_count": 1250,
  "avg_views": 8500,
  "theme": "Технологии",
  "verified": true,
  "created_at": "2023-01-15T10:30:00Z",
  "last_post_date": "2023-12-01T08:45:00Z",
  "connections": [
    {
      "target_id": 2,
      "strength": 0.85,
      "connection_type": "content_similarity",
      "last_updated": "2023-12-01T09:00:00Z"
    }
  ]
}
```

#### POST /channels/{channel_id}/analyze
Запуск анализа канала

**Параметры пути:**
- `channel_id` (integer) - ID канала

**Тело запроса:**
```json
{
  "analysis_types": ["content", "temporal", "network"],
  "depth": 2
}
```

**Ответ:**
```json
{
  "message": "Analysis started",
  "channel_id": 1,
  "task_id": "abc123-def456-ghi789"
}
```

#### POST /channels/import
Импорт нового канала из Telegram

**Тело запроса:**
```json
{
  "username": "@new_channel"
}
```

**Ответ:**
```json
{
  "message": "Channel import started",
  "username": "@new_channel"
}
```

### Анализ

#### GET /analysis/{channel_id}
Получение результатов анализа канала

**Параметры пути:**
- `channel_id` (integer) - ID канала

**Ответ:**
```json
{
  "channel_id": 1,
  "analysis_timestamp": "2023-12-01T12:00:00Z",
  "content_analysis": {
    "duplicate_analysis": {
      "total_duplicates": 15,
      "duplicate_rate": 0.12
    },
    "similarity_analysis": [
      {
        "channel_id": 2,
        "channel_name": "Related Channel",
        "average_similarity": 0.75,
        "max_similarity": 0.92
      }
    ],
    "topic_analysis": {
      "topics": [
        {
          "id": 0,
          "keywords": ["технологии", "AI", "машинное", "обучение"],
          "weight": 0.85
        }
      ]
    }
  },
  "temporal_analysis": {
    "posting_patterns": {
      "hourly_distribution": {
        "9": 15,
        "10": 22,
        "11": 18
      },
      "peak_hours": [10, 11, 14]
    },
    "correlations": [
      {
        "related_channel": {
          "id": 2,
          "name": "Related Channel"
        },
        "hourly_correlation": 0.78,
        "synchronized_posts": 12
      }
    ]
  },
  "network_analysis": {
    "metrics": {
      "degree_centrality": 0.65,
      "pagerank": 0.0234,
      "clustering_coefficient": 0.42,
      "total_connections": 8
    }
  },
  "relationship_summary": {
    "total_connections": 8,
    "strong_connections": 3,
    "confidence_score": 0.82,
    "key_insights": [
      "Высокий уровень дубликатов контента: 12.0%",
      "Обнаружено 2 сильных временных корреляций"
    ]
  }
}
```

### Связи

#### GET /connections
Получение связей между каналами

**Параметры запроса:**
- `source_id` (integer, optional) - ID исходного канала
- `target_id` (integer, optional) - ID целевого канала
- `connection_type` (string, optional) - Тип связи
- `min_strength` (float, optional) - Минимальная сила связи

**Ответ:**
```json
[
  {
    "id": 1,
    "source_id": 1,
    "target_id": 2,
    "connection_type": "content_similarity",
    "strength": 0.85,
    "confidence": 0.92,
    "first_detected": "2023-11-15T14:30:00Z",
    "last_updated": "2023-12-01T09:00:00Z",
    "evidence": {
      "duplicate_posts": 15,
      "similar_topics": 8,
      "time_correlation": 0.72
    }
  }
]
```

### Статистика

#### GET /stats/overview
Получение общей статистики системы

**Ответ:**
```json
{
  "total_channels": 1542,
  "active_channels": 892,
  "total_connections": 3847,
  "total_subscribers": 15420000,
  "themes_distribution": {
    "Технологии": 234,
    "Новости": 189,
    "Политика": 156,
    "Спорт": 98
  },
  "last_updated": "2023-12-01T12:00:00Z"
}
```

## Коды ошибок

- `200` - Успешный запрос
- `400` - Неверный запрос
- `401` - Не авторизован
- `403` - Доступ запрещен
- `404` - Ресурс не найден
- `422` - Ошибка валидации
- `500` - Внутренняя ошибка сервера

**Формат ошибки:**
```json
{
  "detail": "Описание ошибки",
  "error_code": "CHANNEL_NOT_FOUND",
  "timestamp": "2023-12-01T12:00:00Z"
}
```

## Лимиты скорости

- **API запросы:** 100 запросов в минуту на IP
- **Анализ каналов:** 10 запросов в минуту на пользователя
- **Импорт каналов:** 5 запросов в минуту на пользователя

## WebSocket соединения

### /ws/analysis/{channel_id}
Получение обновлений анализа в реальном времени

**Пример сообщения:**
```json
{
  "type": "analysis_progress",
  "channel_id": 1,
  "progress": 0.65,
  "current_step": "content_analysis",
  "estimated_completion": "2023-12-01T12:05:00Z"
}
```

## SDK и библиотеки

### Python
```python
import httpx

class TelegramAnalysisAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    async def get_channels(self, **filters):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/channels",
                headers=self.headers,
                params=filters
            )
            return response.json()
```

### JavaScript
```javascript
class TelegramAnalysisAPI {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }
  
  async getChannels(filters = {}) {
    const params = new URLSearchParams(filters);
    const response = await fetch(`${this.baseUrl}/channels?${params}`, {
      headers: this.headers
    });
    return response.json();
  }
}
```
