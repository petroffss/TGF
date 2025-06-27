# main.py - Основной API сервер
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import uvicorn
from datetime import datetime, timedelta
import logging
import os

# Модели данных
class Channel(BaseModel):
    id: int
    name: str
    username: str
    description: str
    subscribers: int
    theme: str
    posts: int
    avg_views: int
    created_at: datetime
    last_post: datetime
    verified: bool
    connections: List[Dict[str, Any]] = []

class ChannelConnection(BaseModel):
    source_id: int
    target_id: int
    connection_type: str
    strength: float
    last_updated: datetime
    metadata: Dict[str, Any] = {}

class AnalysisRequest(BaseModel):
    channel_id: int
    analysis_types: List[str] = ["content", "temporal", "network"]
    depth: int = 2

class AnalysisResult(BaseModel):
    channel_id: int
    connected_channels: List[Dict[str, Any]]
    network_metrics: Dict[str, float]
    content_analysis: Dict[str, Any]
    time_analysis: Dict[str, Any]
    created_at: datetime

# Инициализация приложения
app = FastAPI(
    title="Telegram Channels Analysis API",
    description="API для анализа взаимосвязанных каналов Telegram",
    version="1.0.0"
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Имитация базы данных
channels_db = {}
connections_db = {}
analysis_results_db = {}

# Сервисы и утилиты
class TelegramDataCollector:
    """Модуль сбора данных из Telegram API"""
    
    def __init__(self, api_id: str, api_hash: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.client = None
    
    async def connect(self):
        """Подключение к Telegram API"""
        # Здесь была бы реальная инициализация Telethon/Pyrogram
        pass
    
    async def get_channel_info(self, channel_username: str) -> Dict[str, Any]:
        """Получение информации о канале"""
        # Имитация данных
        return {
            "name": f"Channel {channel_username}",
            "username": channel_username,
            "description": "Channel description",
            "subscribers": 10000,
            "posts_count": 500
        }
    
    async def get_channel_posts(self, channel_id: int, limit: int = 100) -> List[Dict]:
        """Получение постов канала"""
        # Имитация постов
        posts = []
        for i in range(limit):
            posts.append({
                "id": i,
                "text": f"Post {i} content",
                "date": datetime.now() - timedelta(days=i),
                "views": 1000 + i * 10,
                "media": []
            })
        return posts

class ContentAnalyzer:
    """Модуль анализа контента"""
    
    @staticmethod
    def calculate_content_similarity(text1: str, text2: str) -> float:
        """Вычисление семантической схожести текстов"""
        # Упрощенная реализация
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def detect_duplicates(posts: List[Dict]) -> List[Dict]:
        """Обнаружение дубликатов контента"""
        duplicates = []
        for i, post1 in enumerate(posts):
            for j, post2 in enumerate(posts[i+1:], i+1):
                similarity = ContentAnalyzer.calculate_content_similarity(
                    post1.get("text", ""), 
                    post2.get("text", "")
                )
                if similarity > 0.8:
                    duplicates.append({
                        "post1_id": post1["id"],
                        "post2_id": post2["id"],
                        "similarity": similarity
                    })
        return duplicates
    
    @staticmethod
    def extract_keywords(text: str, top_k: int = 10) -> List[str]:
        """Извлечение ключевых слов"""
        # Упрощенная реализация
        words = text.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Фильтруем короткие слова
                word_freq[word] = word_freq.get(word, 0) + 1
        
        return sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:top_k]

class NetworkAnalyzer:
    """Модуль анализа сетей"""
    
    @staticmethod
    def calculate_centrality(connections: List[ChannelConnection], channel_id: int) -> float:
        """Вычисление центральности узла"""
        in_degree = sum(1 for conn in connections if conn.target_id == channel_id)
        out_degree = sum(1 for conn in connections if conn.source_id == channel_id)
        total_nodes = len(set([conn.source_id for conn in connections] + [conn.target_id for conn in connections]))
        
        return (in_degree + out_degree) / (2 * (total_nodes - 1)) if total_nodes > 1 else 0.0
    
    @staticmethod
    def find_communities(connections: List[ChannelConnection]) -> Dict[int, int]:
        """Обнаружение сообществ в сети"""
        # Упрощенная реализация кластеризации
        # В реальности использовался бы алгоритм Лувена или подобный
        communities = {}
        community_id = 0
        
        nodes = set()
        for conn in connections:
            nodes.add(conn.source_id)
            nodes.add(conn.target_id)
        
        for node in nodes:
            communities[node] = community_id % 5  # Распределяем по 5 сообществам
            community_id += 1
        
        return communities

class TemporalAnalyzer:
    """Модуль временного анализа"""
    
    @staticmethod
    def calculate_time_correlation(posts1: List[Dict], posts2: List[Dict]) -> float:
        """Вычисление временной корреляции между каналами"""
        # Упрощенная реализация
        if not posts1 or not posts2:
            return 0.0
        
        # Группируем посты по часам
        hours1 = [post["date"].hour for post in posts1]
        hours2 = [post["date"].hour for post in posts2]
        
        # Вычисляем корреляцию активности по часам
        correlation = 0.0
        for hour in range(24):
            count1 = hours1.count(hour)
            count2 = hours2.count(hour)
            correlation += min(count1, count2)
        
        return correlation / max(len(posts1), len(posts2))
    
    @staticmethod
    def detect_synchronized_posting(posts1: List[Dict], posts2: List[Dict], 
                                  threshold_minutes: int = 30) -> List[Dict]:
        """Обнаружение синхронных публикаций"""
        synchronized = []
        
        for post1 in posts1:
            for post2 in posts2:
                time_diff = abs((post1["date"] - post2["date"]).total_seconds() / 60)
                if time_diff <= threshold_minutes:
                    synchronized.append({
                        "post1_id": post1["id"],
                        "post2_id": post2["id"],
                        "time_diff_minutes": time_diff
                    })
        
        return synchronized

# Инициализация сервисов
# Читаем учетные данные из переменных окружения
telegram_collector = TelegramDataCollector(
    os.getenv("TELEGRAM_API_ID", ""),
    os.getenv("TELEGRAM_API_HASH", "")
)
content_analyzer = ContentAnalyzer()
network_analyzer = NetworkAnalyzer()
temporal_analyzer = TemporalAnalyzer()

# API эндпоинты

@app.get("/")
async def root():
    return {"message": "Telegram Channels Analysis API", "version": "1.0.0"}

@app.get("/channels", response_model=List[Channel])
async def get_channels(
    search: Optional[str] = None,
    theme: Optional[str] = None,
    min_subscribers: int = 0,
    limit: int = 50
):
    """Получение списка каналов с фильтрацией"""
    channels = list(channels_db.values())
    
    # Применяем фильтры
    if search:
        channels = [ch for ch in channels if search.lower() in ch.name.lower() or 
                   search.lower() in ch.username.lower()]
    
    if theme:
        channels = [ch for ch in channels if ch.theme == theme]
    
    if min_subscribers:
        channels = [ch for ch in channels if ch.subscribers >= min_subscribers]
    
    return channels[:limit]

@app.get("/channels/{channel_id}", response_model=Channel)
async def get_channel(channel_id: int):
    """Получение информации о конкретном канале"""
    if channel_id not in channels_db:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    return channels_db[channel_id]

@app.post("/channels/{channel_id}/analyze")
async def analyze_channel(
    channel_id: int, 
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """Запуск анализа канала"""
    if channel_id not in channels_db:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Запускаем анализ в фоне
    background_tasks.add_task(perform_channel_analysis, channel_id, request)
    
    return {"message": "Analysis started", "channel_id": channel_id}

@app.get("/analysis/{channel_id}")
async def get_analysis_results(channel_id: int):
    """Получение результатов анализа"""
    if channel_id not in analysis_results_db:
        raise HTTPException(status_code=404, detail="Analysis results not found")
    
    return analysis_results_db[channel_id]

@app.get("/connections")
async def get_connections(
    source_id: Optional[int] = None,
    target_id: Optional[int] = None,
    connection_type: Optional[str] = None
):
    """Получение связей между каналами"""
    connections = list(connections_db.values())
    
    if source_id:
        connections = [conn for conn in connections if conn.source_id == source_id]
    
    if target_id:
        connections = [conn for conn in connections if conn.target_id == target_id]
    
    if connection_type:
        connections = [conn for conn in connections if conn.connection_type == connection_type]
    
    return connections

@app.post("/channels/import")
async def import_channel(username: str, background_tasks: BackgroundTasks):
    """Импорт нового канала из Telegram"""
    # Проверяем, что канал не существует
    existing = [ch for ch in channels_db.values() if ch.username == username]
    if existing:
        raise HTTPException(status_code=400, detail="Channel already exists")
    
    # Запускаем импорт в фоне
    background_tasks.add_task(import_channel_data, username)
    
    return {"message": "Channel import started", "username": username}

@app.get("/stats/overview")
async def get_overview_stats():
    """Получение общей статистики системы"""
    total_channels = len(channels_db)
    total_connections = len(connections_db)
    total_subscribers = sum(ch.subscribers for ch in channels_db.values())
    
    # Статистика по темам
    themes_stats = {}
    for channel in channels_db.values():
        themes_stats[channel.theme] = themes_stats.get(channel.theme, 0) + 1
    
    return {
        "total_channels": total_channels,
        "total_connections": total_connections,
        "total_subscribers": total_subscribers,
        "themes_distribution": themes_stats,
        "last_updated": datetime.now()
    }

# Фоновые задачи

async def perform_channel_analysis(channel_id: int, request: AnalysisRequest):
    """Выполнение анализа канала"""
    try:
        channel = channels_db[channel_id]
        
        # Получаем посты канала
        posts = await telegram_collector.get_channel_posts(channel_id)
        
        # Найти связанные каналы
        related_connections = [conn for conn in connections_db.values() 
                             if conn.source_id == channel_id or conn.target_id == channel_id]
        
        connected_channels = []
        for conn in related_connections:
            target_id = conn.target_id if conn.source_id == channel_id else conn.source_id
            if target_id in channels_db:
                connected_channels.append({
                    "channel": channels_db[target_id],
                    "connection": conn
                })
        
        # Анализ контента
        content_analysis = {}
        if "content" in request.analysis_types:
            duplicates = content_analyzer.detect_duplicates(posts)
            keywords = content_analyzer.extract_keywords(" ".join([p.get("text", "") for p in posts]))
            
            content_analysis = {
                "duplicates_count": len(duplicates),
                "duplicate_percentage": len(duplicates) / len(posts) * 100 if posts else 0,
                "keywords": keywords,
                "average_similarity": sum(d["similarity"] for d in duplicates) / len(duplicates) if duplicates else 0
            }
        
        # Временной анализ
        time_analysis = {}
        if "temporal" in request.analysis_types:
            # Анализ активности по часам
            hourly_activity = {}
            for post in posts:
                hour = post["date"].hour
                hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
            
            peak_hour = max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else 0
            
            time_analysis = {
                "hourly_activity": hourly_activity,
                "peak_activity_hour": peak_hour,
                "total_posts": len(posts),
                "average_posts_per_day": len(posts) / 30  # За последние 30 дней
            }
        
        # Сетевой анализ
        network_metrics = {}
        if "network" in request.analysis_types:
            all_connections = list(connections_db.values())
            centrality = network_analyzer.calculate_centrality(all_connections, channel_id)
            communities = network_analyzer.find_communities(all_connections)
            
            network_metrics = {
                "centrality": centrality,
                "community_id": communities.get(channel_id, 0),
                "connections_count": len(related_connections),
                "clustering_coefficient": centrality * 0.8  # Упрощенное вычисление
            }
        
        # Сохраняем результаты
        analysis_results_db[channel_id] = AnalysisResult(
            channel_id=channel_id,
            connected_channels=connected_channels,
            network_metrics=network_metrics,
            content_analysis=content_analysis,
            time_analysis=time_analysis,
            created_at=datetime.now()
        )
        
        logging.info(f"Analysis completed for channel {channel_id}")
        
    except Exception as e:
        logging.error(f"Analysis failed for channel {channel_id}: {str(e)}")

async def import_channel_data(username: str):
    """Импорт данных канала из Telegram"""
    try:
        # Получаем информацию о канале
        channel_info = await telegram_collector.get_channel_info(username)
        
        # Создаем новый канал
        channel_id = len(channels_db) + 1
        new_channel = Channel(
            id=channel_id,
            name=channel_info["name"],
            username=username,
            description=channel_info["description"],
            subscribers=channel_info["subscribers"],
            theme="Импортированный",  # Потом можно добавить автоматическое определение темы
            posts=channel_info["posts_count"],
            avg_views=channel_info["subscribers"] // 10,  # Примерная оценка
            created_at=datetime.now() - timedelta(days=365),
            last_post=datetime.now(),
            verified=False,
            connections=[]
        )
        
        channels_db[channel_id] = new_channel
        
        logging.info(f"Channel {username} imported successfully with ID {channel_id}")
        
    except Exception as e:
        logging.error(f"Failed to import channel {username}: {str(e)}")

# Инициализация тестовых данных
async def initialize_test_data():
    """Инициализация тестовых данных"""
    themes = ['Политика', 'Технологии', 'Новости', 'Спорт', 'Бизнес', 'Развлечения']
    
    # Создаем тестовые каналы
    for i in range(1, 51):
        channel = Channel(
            id=i,
            name=f"Канал {i}",
            username=f"@channel{i}",
            description=f"Описание канала {i} - качественный контент",
            subscribers=1000 + i * 1000,
            theme=themes[i % len(themes)],
            posts=100 + i * 10,
            avg_views=500 + i * 100,
            created_at=datetime.now() - timedelta(days=365 - i * 7),
            last_post=datetime.now() - timedelta(hours=i),
            verified=i % 10 == 0,
            connections=[]
        )
        channels_db[i] = channel
    
    # Создаем тестовые связи
    connection_types = ['content_similarity', 'time_correlation', 'admin_overlap', 'cross_posting']
    connection_id = 1
    
    for i in range(1, 51):
        # Каждый канал связан с 3-7 другими каналами
        num_connections = 3 + (i % 5)
        for j in range(num_connections):
            target_id = ((i + j * 7) % 50) + 1
            if target_id != i:
                connection = ChannelConnection(
                    source_id=i,
                    target_id=target_id,
                    connection_type=connection_types[j % len(connection_types)],
                    strength=0.3 + (i * j % 100) / 100 * 0.7,
                    last_updated=datetime.now() - timedelta(days=j),
                    metadata={}
                )
                connections_db[connection_id] = connection
                connection_id += 1

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    await initialize_test_data()
    logging.info("Test data initialized")

# Запуск сервера
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
