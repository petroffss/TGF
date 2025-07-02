# main.py - Основной API сервер
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials # Not used yet
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
import uvicorn  # Keep for local running, but not strictly for lib code
from datetime import datetime, timedelta
import logging
import os

from sqlalchemy.orm import Session
import database as db_models # Renamed to avoid conflicts with pydantic models
from database import get_db, create_tables, SessionLocal

# Pydantic Schemas for API requests and responses

class ChannelBaseSchema(BaseModel):
    username: str
    name: Optional[str] = None
    description: Optional[str] = None
    theme: Optional[str] = None
    language: Optional[str] = 'ru'
    verified: Optional[bool] = False
    subscribers_count: Optional[int] = 0
    posts_count: Optional[int] = 0
    avg_views: Optional[int] = 0
    telegram_id: Optional[str] = None
    last_post_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class ChannelCreateSchema(ChannelBaseSchema):
    pass

class ChannelConnectionSchema(BaseModel):
    id: int
    source_id: int
    target_id: int
    connection_type: str
    strength: Optional[float] = 0.0
    confidence: Optional[float] = 0.0
    posts_overlap: Optional[int] = 0
    time_correlation: Optional[float] = 0.0
    content_similarity: Optional[float] = 0.0
    first_detected: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    evidence: Optional[Dict[str, Any]] = None
    model_config = ConfigDict(from_attributes=True)


class ChannelSchema(ChannelBaseSchema):
    id: int
    created_at: datetime
    last_updated: datetime
    # connections: List[ChannelConnectionSchema] = [] # TODO: Revisit how to populate this

    model_config = ConfigDict(from_attributes=True)


class AnalysisRequestSchema(BaseModel): # Renamed from AnalysisRequest
    channel_id: int
    analysis_types: List[str] = ["content", "temporal", "network"]
    depth: int = 2

class AnalysisResultSchema(BaseModel): # Renamed from AnalysisResult, structure might change based on DB
    channel_id: int
    # Fields below are based on the old mock structure, will need to align with AnalysisTask model
    connected_channels: List[Dict[str, Any]] # This likely needs to be List[ChannelSchema] or similar
    network_metrics: Dict[str, float]
    content_analysis: Dict[str, Any]
    time_analysis: Dict[str, Any]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


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

# # Имитация базы данных - REMOVING THESE
# channels_db = {}
# connections_db = {}
# analysis_results_db = {}

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

@app.get("/channels", response_model=List[ChannelSchema])
async def get_channels(
    db: Session = Depends(get_db),
    search: Optional[str] = None,
    theme: Optional[str] = None,
    min_subscribers: int = 0,
    limit: int = 50
):
    """Получение списка каналов с фильтрацией"""
    query = db.query(db_models.Channel)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            (db_models.Channel.name.ilike(search_term)) |
            (db_models.Channel.username.ilike(search_term))
        )

    if theme:
        query = query.filter(db_models.Channel.theme == theme)

    if min_subscribers > 0:
        query = query.filter(db_models.Channel.subscribers_count >= min_subscribers)

    channels = query.limit(limit).all()
    return channels

@app.get("/channels/{channel_id}", response_model=ChannelSchema)
async def get_channel(channel_id: int, db: Session = Depends(get_db)):
    """Получение информации о конкретном канале"""
    db_channel = db.query(db_models.Channel).filter(db_models.Channel.id == channel_id).first()
    if db_channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")
    return db_channel

@app.post("/channels/{channel_id}/analyze")
async def analyze_channel(
    channel_id: int,
    request: AnalysisRequestSchema, # Changed from AnalysisRequest
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Запуск анализа канала"""
    db_channel = db.query(db_models.Channel).filter(db_models.Channel.id == channel_id).first()
    if db_channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    # The background task will need its own DB session.
    background_tasks.add_task(perform_channel_analysis, channel_id, request)

    return {"message": "Analysis started", "channel_id": channel_id}

@app.get("/analysis/{channel_id}", response_model=Optional[AnalysisResultSchema]) # Changed from AnalysisResult
async def get_analysis_results(channel_id: int, db: Session = Depends(get_db)):
    """Получение результатов анализа"""
    # This endpoint will now fetch from AnalysisTask table
    analysis_task = db.query(db_models.AnalysisTask).filter(
        db_models.AnalysisTask.channel_id == channel_id
    ).order_by(db_models.AnalysisTask.created_at.desc()).first()

    if analysis_task is None:
        raise HTTPException(status_code=404, detail="Analysis task not found for this channel.")

    if analysis_task.status != 'completed' or analysis_task.results is None:
        return { # Or some other response indicating task is pending/failed
            "channel_id": channel_id,
            "status": analysis_task.status,
            "message": "Analysis results are not yet available or task is not completed.",
            "created_at": analysis_task.created_at,
            "updated_at": analysis_task.completed_at or analysis_task.started_at or analysis_task.created_at
        }

    # Assuming analysis_task.results is a dict that matches AnalysisResultSchema structure
    # This might need careful construction in perform_channel_analysis
    try:
        # We need to ensure the structure of analysis_task.results matches AnalysisResultSchema
        # This is a placeholder conversion.
        # A more robust solution would be to ensure `perform_channel_analysis` stores results
        # in the exact structure `AnalysisResultSchema` expects, or have a dedicated
        # schema for `AnalysisTask.results` JSON field.
        return AnalysisResultSchema(
            channel_id=analysis_task.channel_id,
            connected_channels=analysis_task.results.get("connected_channels", []),
            network_metrics=analysis_task.results.get("network_metrics", {}),
            content_analysis=analysis_task.results.get("content_analysis", {}),
            time_analysis=analysis_task.results.get("time_analysis", {}),
            created_at=analysis_task.completed_at # Should be completion time of analysis
        )
    except Exception as e: # Catch potential pydantic validation errors if structure is wrong
        logging.error(f"Error converting analysis task results to schema for channel {channel_id}: {e}")
        raise HTTPException(status_code=500, detail="Error processing analysis results.")


@app.get("/connections", response_model=List[ChannelConnectionSchema])
async def get_connections(
    db: Session = Depends(get_db),
    source_id: Optional[int] = None,
    target_id: Optional[int] = None,
    connection_type: Optional[str] = None
):
    """Получение связей между каналами"""
    query = db.query(db_models.ChannelConnection)

    if source_id:
        query = query.filter(db_models.ChannelConnection.source_id == source_id)

    if target_id:
        query = query.filter(db_models.ChannelConnection.target_id == target_id)

    if connection_type:
        query = query.filter(db_models.ChannelConnection.connection_type == connection_type)

    connections = query.all()
    return connections

@app.post("/channels/import")
async def import_channel(
    username: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Импорт нового канала из Telegram"""
    existing_channel = db.query(db_models.Channel).filter(db_models.Channel.username == username).first()
    if existing_channel:
        raise HTTPException(status_code=400, detail=f"Channel @{username} already exists with ID {existing_channel.id}")

    # The background task will need its own DB session.
    background_tasks.add_task(import_channel_data, username)

    return {"message": f"Channel import for @{username} started"}

@app.get("/stats/overview")
async def get_overview_stats(db: Session = Depends(get_db)):
    """Получение общей статистики системы"""
    total_channels = db.query(db_models.Channel).count()
    total_connections = db.query(db_models.ChannelConnection).count()

    # For total_subscribers, handle potential None values if not all channels have it set
    total_subscribers_query_result = db.query(db_models.func.sum(db_models.Channel.subscribers_count)).scalar()
    total_subscribers = total_subscribers_query_result if total_subscribers_query_result is not None else 0

    themes_stats_query = db.query(
        db_models.Channel.theme,
        db_models.func.count(db_models.Channel.id)
    ).group_by(db_models.Channel.theme).all()

    themes_stats = {theme: count for theme, count in themes_stats_query}

    return {
        "total_channels": total_channels,
        "total_connections": total_connections,
        "total_subscribers": total_subscribers,
        "themes_distribution": themes_stats,
        "last_updated": datetime.now() # This should ideally reflect data update time
    }

# Фоновые задачи

async def perform_channel_analysis(channel_id: int, request: AnalysisRequestSchema): # Use new schema
    """Выполнение анализа канала. This task needs its own DB session."""
    db: Session = SessionLocal()
    try:
        # Fetch channel from DB
        db_channel = db.query(db_models.Channel).filter(db_models.Channel.id == channel_id).first()
        if not db_channel:
            logging.error(f"perform_channel_analysis: Channel {channel_id} not found.")
            return

        # Placeholder for analysis task creation/update
        analysis_task = db_models.AnalysisTask(
            channel_id=channel_id,
            analysis_type=", ".join(request.analysis_types), # Store as string or handle differently
            status='running',
            started_at=datetime.utcnow()
        )
        db.add(analysis_task)
        db.commit()
        db.refresh(analysis_task)

        logging.info(f"Starting analysis for channel {channel_id}, task ID {analysis_task.id}")

        # Mock data fetching and analysis logic (to be replaced with real implementations)
        posts = await telegram_collector.get_channel_posts(channel_id) # Still uses mock collector

        # Mock related connections query (replace with actual DB query if needed for analysis)
        # For now, this part of the original logic that used in-memory `connections_db`
        # needs to be adapted or the analysis logic itself needs to query DB for connections.
        # Let's assume for now the analysis will focus on the channel's own posts.
        # If cross-channel analysis is needed, this part needs more work.

        # --- Mock analysis result structure ---
        # This structure should eventually be built by actual analysis modules.
        # The current ContentAnalyzer etc classes are simplified.

        results_data = {
            "connected_channels": [], # Placeholder, this would involve querying DBChannelConnection
            "network_metrics": {},
            "content_analysis": {},
            "time_analysis": {}
        }

        if "content" in request.analysis_types:
            # This still uses the simplified ContentAnalyzer
            # In a real scenario, ContentAnalyzer would likely use db_channel.posts relationship
            raw_posts_text = " ".join([p.get("text", "") for p in posts]) # posts are mock data
            keywords = content_analyzer.extract_keywords(raw_posts_text)
            # Duplicates detection would need actual post data from DB or collector.
            results_data["content_analysis"] = {
                "keywords": keywords,
                "duplicates_count": 0, # Placeholder
                "duplicate_percentage": 0.0, # Placeholder
                "average_similarity": 0.0 # Placeholder
            }

        if "temporal" in request.analysis_types:
            # Similar to content, this uses mock posts
            hourly_activity = {}
            if posts:
                for post_data in posts: # posts is mock data
                    hour = post_data["date"].hour # Assuming mock posts have datetime objects
                    hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
            peak_hour = max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else None
            results_data["time_analysis"] = {
                 "hourly_activity": hourly_activity,
                 "peak_activity_hour": peak_hour,
                 "total_posts": len(posts), # Based on mock posts
                 "average_posts_per_day": len(posts) / 30 if posts else 0 # Mock calculation
            }

        # Network analysis placeholder
        if "network" in request.analysis_types:
             # Actual network analysis would query DBChannelConnection table
             # using db_channel.id and apply graph algorithms.
            results_data["network_metrics"] = {
                "centrality": 0.0, # Placeholder
                "community_id": 0, # Placeholder
                "connections_count": 0, # Placeholder
                "clustering_coefficient": 0.0 # Placeholder
            }

        # Update AnalysisTask with results
        analysis_task.results = results_data
        analysis_task.status = 'completed'
        analysis_task.completed_at = datetime.utcnow()
        db.commit()

        logging.info(f"Analysis completed for channel {channel_id}, task ID {analysis_task.id}")

    except Exception as e:
        db.rollback()
        logging.error(f"Analysis failed for channel {channel_id}: {str(e)}")
        if 'analysis_task' in locals() and analysis_task: # Check if task object exists
            analysis_task.status = 'failed'
            analysis_task.error_message = str(e)
            analysis_task.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()

async def import_channel_data(username: str): # No change to signature, but implementation uses DB
    """Импорт данных канала из Telegram. This task needs its own DB session."""
    db: Session = SessionLocal()
    try:
        # Check again if channel exists, in case of race condition with API endpoint check
        existing_channel = db.query(db_models.Channel).filter(db_models.Channel.username == username).first()
        if existing_channel:
            logging.info(f"Channel @{username} already exists in DB (ID: {existing_channel.id}). Skipping import.")
            return

        channel_info = await telegram_collector.get_channel_info(username) # Still uses mock collector

        new_db_channel = db_models.Channel(
            name=channel_info.get("name", username), # Use username if name not provided
            username=username,
            description=channel_info.get("description"),
            subscribers_count=channel_info.get("subscribers", 0),
            posts_count=channel_info.get("posts_count",0),
            # theme="Импортированный", # Let theme be optional or set by analysis
            # avg_views=channel_info.get("subscribers", 0) // 10, # Example, might not be accurate
            created_at=datetime.utcnow(), # Record when we added it
            last_updated=datetime.utcnow()
            # telegram_id, last_post_date would come from actual collector
        )

        db.add(new_db_channel)
        db.commit()
        db.refresh(new_db_channel)

        logging.info(f"Channel @{username} imported successfully into DB with ID {new_db_channel.id}")

    except Exception as e:
        db.rollback()
        logging.error(f"Failed to import channel @{username} into DB: {str(e)}")
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    create_tables() # Create database tables if they don't exist
    logging.info("Database tables checked/created.")
    # await initialize_test_data() # Removing mock data initialization
    # logging.info("Test data initialized")

# Запуск сервера
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
