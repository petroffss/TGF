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
