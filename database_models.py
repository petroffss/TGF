# database.py - Модели и схемы базы данных
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Index, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid

# Настройки подключения к базе данных
DATABASE_URL = "postgresql://username:password@localhost/telegram_analysis"

# Создание движка и сессии
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модели данных

class Channel(Base):
    """Модель канала Telegram"""
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)  # ID канала в Telegram
    username = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    subscribers_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    avg_views = Column(Integer, default=0)
    theme = Column(String, index=True)
    language = Column(String, default='ru')
    verified = Column(Boolean, default=False)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    last_post_date = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Статистика активности
    daily_posts_avg = Column(Float, default=0.0)
    engagement_rate = Column(Float, default=0.0)
    
    # JSON поля для дополнительных данных
    metadata = Column(JSON)
    
    # Связи
    posts = relationship("Post", back_populates="channel", cascade="all, delete-orphan")
    source_connections = relationship("ChannelConnection", foreign_keys="ChannelConnection.source_id", back_populates="source_channel")
    target_connections = relationship("ChannelConnection", foreign_keys="ChannelConnection.target_id", back_populates="target_channel")
    
    # Индексы для оптимизации
    __table_args__ = (
        Index('idx_channel_theme_subscribers', 'theme', 'subscribers_count'),
        Index('idx_channel_activity', 'last_post_date', 'posts_count'),
    )

class Post(Base):
    """Модель поста канала"""
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, index=True)  # ID поста в Telegram
    channel_id = Column(Integer, ForeignKey("channels.id"), index=True)
    
    # Содержимое
    text = Column(Text)
    text_hash = Column(String, index=True)  # Хеш для быстрого поиска дубликатов
    
    # Метрики
    views = Column(Integer, default=0)
    reactions_count = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)
    forwards_count = Column(Integer, default=0)
    
    # Временные метки
    published_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Медиа и файлы
    has_media = Column(Boolean, default=False)
    media_type = Column(String)  # photo, video, document, etc.
    media_hash = Column(String, index=True)  # Хеш медиафайла
    
    # JSON поля
    hashtags = Column(ARRAY(String))
    mentions = Column(ARRAY(String))
    links = Column(ARRAY(String))
    metadata = Column(JSON)
    
    # Связи
    channel = relationship("Channel", back_populates="posts")
    duplicates = relationship("PostDuplicate", foreign_keys="PostDuplicate.original_post_id", back_populates="original_post")
    
    # Индексы
    __table_args__ = (
        Index('idx_post_time_channel', 'published_at', 'channel_id'),
        Index('idx_post_hash', 'text_hash', 'media_hash'),
    )

class ChannelConnection(Base):
    """Модель связи между каналами"""
    __tablename__ = "channel_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("channels.id"), index=True)
    target_id = Column(Integer, ForeignKey("channels.id"), index=True)
    
    # Тип связи
    connection_type = Column(String, index=True)  # content_similarity, time_correlation, admin_overlap, cross_posting
    
    # Метрики связи
    strength = Column(Float, default=0.0, index=True)  # Сила связи от 0 до 1
    confidence = Column(Float, default=0.0)  # Уверенность в связи
    
    # Детали связи
    posts_overlap = Column(Integer, default=0)
    time_correlation = Column(Float, default=0.0)
    content_similarity = Column(Float, default=0.0)
    
    # Временные метки
    first_detected = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime)
    
    # JSON метаданные
    evidence = Column(JSON)  # Доказательства связи
    
    # Связи
    source_channel = relationship("Channel", foreign_keys=[source_id], back_populates="source_connections")
    target_channel = relationship("Channel", foreign_keys=[target_id], back_populates="target_connections")
    
    # Индексы
    __table_args__ = (
        Index('idx_connection_type_strength', 'connection_type', 'strength'),
        Index('idx_connection_channels', 'source_id', 'target_id'),
    )

class PostDuplicate(Base):
    """Модель дубликатов постов"""
    __tablename__ = "post_duplicates"
    
    id = Column(Integer, primary_key=True, index=True)
    original_post_id = Column(Integer, ForeignKey("posts.id"), index=True)
    duplicate_post_id = Column(Integer, ForeignKey("posts.id"), index=True)
    
    # Метрики схожести
    text_similarity = Column(Float, default=0.0)
    media_similarity = Column(Float, default=0.0)
    overall_similarity = Column(Float, default=0.0, index=True)
    
    # Временная разница
    time_diff_minutes = Column(Integer)  # Разница во времени публикации
    
    # Тип дубликата
    duplicate_type = Column(String)  # exact, partial, semantic, media
    
    # Временные метки
    detected_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    original_post = relationship("Post", foreign_keys=[original_post_id], back_populates="duplicates")
    duplicate_post = relationship("Post", foreign_keys=[duplicate_post_id])
    
    # Индексы
    __table_args__ = (
        Index('idx_duplicate_similarity', 'overall_similarity', 'duplicate_type'),
    )

class AnalysisTask(Base):
    """Модель задач анализа"""
    __tablename__ = "analysis_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    
    # Параметры задачи
    channel_id = Column(Integer, ForeignKey("channels.id"))
    analysis_type = Column(String)  # content, temporal, network, full
    status = Column(String, default='pending')  # pending, running, completed, failed
    
    # Прогресс
    progress = Column(Float, default=0.0)
    current_step = Column(String)
    
    # Результаты
    results = Column(JSON)
    error_message = Column(Text)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Связи
    channel = relationship("Channel")

class NetworkMetrics(Base):
    """Модель сетевых метрик каналов"""
    __tablename__ = "network_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), unique=True)
    
    # Метрики центральности
    degree_centrality = Column(Float, default=0.0)
    betweenness_centrality = Column(Float, default=0.0)
    closeness_centrality = Column(Float, default=0.0)
    eigenvector_centrality = Column(Float, default=0.0)
    pagerank = Column(Float, default=0.0)
    
    # Метрики кластеризации
    clustering_coefficient = Column(Float, default=0.0)
    community_id = Column(Integer)
    
    # Статистика связей
    in_degree = Column(Integer, default=0)
    out_degree = Column(Integer, default=0)
    strong_connections = Column(Integer, default=0)  # Связи с силой > 0.7
    
    # Временные метки
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    channel = relationship("Channel")

class ContentKeyword(Base):
    """Модель ключевых слов и тем"""
    __tablename__ = "content_keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), index=True)
    
    # Ключевое слово/тема
    keyword = Column(String, index=True)
    frequency = Column(Integer, default=0)
    weight = Column(Float, default=0.0)  # TF-IDF вес
    
    # Временной период
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    
    # Связи
    channel = relationship("Channel")
    
    # Индексы
    __table_args__ = (
        Index('idx_keyword_frequency', 'keyword', 'frequency'),
        Index('idx_channel_keyword', 'channel_id', 'keyword'),
    )

class ActivityPattern(Base):
    """Модель паттернов активности"""
    __tablename__ = "activity_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), index=True)
    
    # Временные паттерны
    hour_of_day = Column(Integer)  # 0-23
    day_of_week = Column(Integer)  # 0-6
    posts_count = Column(Integer, default=0)
    avg_views = Column(Float, default=0.0)
    
    # Период анализа
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    
    # Связи
    channel = relationship("Channel")
    
    # Индексы
    __table_args__ = (
        Index('idx_activity_time', 'hour_of_day', 'day_of_week'),
    )

# Вспомогательные функции для работы с базой данных

def get_db():
    """Получение сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Создание всех таблиц"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Удаление всех таблиц"""
    Base.metadata.drop_all(bind=engine)

# Функции для работы с данными

class DatabaseManager:
    """Менеджер для работы с базой данных"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_channel_by_username(self, username: str) -> Channel:
        """Получить канал по username"""
        return self.db.query(Channel).filter(Channel.username == username).first()
    
    def get_channels_by_theme(self, theme: str) -> list:
        """Получить каналы по теме"""
        return self.db.query(Channel).filter(Channel.theme == theme).all()
    
    def get_channel_connections(self, channel_id: int, min_strength: float = 0.0) -> list:
        """Получить связи канала"""
        return self.db.query(ChannelConnection).filter(
            (ChannelConnection.source_id == channel_id) | 
            (ChannelConnection.target_id == channel_id),
            ChannelConnection.strength >= min_strength
        ).all()
    
    def find_duplicate_posts(self, channel_id: int, similarity_threshold: float = 0.8) -> list:
        """Найти дубликаты постов"""
        return self.db.query(PostDuplicate).join(Post, PostDuplicate.original_post_id == Post.id).filter(
            Post.channel_id == channel_id,
            PostDuplicate.overall_similarity >= similarity_threshold
        ).all()
    
    def get_network_metrics(self, channel_id: int) -> NetworkMetrics:
        """Получить сетевые метрики канала"""
        return self.db.query(NetworkMetrics).filter(NetworkMetrics.channel_id == channel_id).first()
    
    def get_top_keywords(self, channel_id: int, limit: int = 10) -> list:
        """Получить топ ключевых слов канала"""
        return self.db.query(ContentKeyword).filter(
            ContentKeyword.channel_id == channel_id
        ).order_by(ContentKeyword.weight.desc()).limit(limit).all()
    
    def get_activity_pattern(self, channel_id: int) -> list:
        """Получить паттерн активности канала"""
        return self.db.query(ActivityPattern).filter(
            ActivityPattern.channel_id == channel_id
        ).all()
    
    def create_channel(self, channel_data: dict) -> Channel:
        """Создать новый канал"""
        channel = Channel(**channel_data)
        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)
        return channel
    
    def update_channel_stats(self, channel_id: int, stats: dict):
        """Обновить статистику канала"""
        channel = self.db.query(Channel).filter(Channel.id == channel_id).first()
        if channel:
            for key, value in stats.items():
                setattr(channel, key, value)
            channel.last_updated = datetime.utcnow()
            self.db.commit()
    
    def create_connection(self, connection_data: dict) -> ChannelConnection:
        """Создать связь между каналами"""
        # Проверяем, не существует ли уже такая связь
        existing = self.db.query(ChannelConnection).filter(
            ChannelConnection.source_id == connection_data['source_id'],
            ChannelConnection.target_id == connection_data['target_id'],
            ChannelConnection.connection_type == connection_data['connection_type']
        ).first()
        
        if existing:
            # Обновляем существующую связь
            for key, value in connection_data.items():
                setattr(existing, key, value)
            existing.last_updated = datetime.utcnow()
            self.db.commit()
            return existing
        else:
            # Создаем новую связь
            connection = ChannelConnection(**connection_data)
            self.db.add(connection)
            self.db.commit()
            self.db.refresh(connection)
            return connection
    
    def bulk_insert_posts(self, posts_data: list):
        """Массовая вставка постов"""
        posts = [Post(**post_data) for post_data in posts_data]
        self.db.bulk_save_objects(posts)
        self.db.commit()
    
    def get_channels_for_analysis(self, limit: int = 100) -> list:
        """Получить каналы для анализа (давно не обновлявшиеся)"""
        cutoff_date = datetime.utcnow() - timedelta(hours=24)
        return self.db.query(Channel).filter(
            Channel.last_updated < cutoff_date
        ).limit(limit).all()

# SQL-запросы для аналитики

POPULAR_THEMES_QUERY = """
SELECT theme, COUNT(*) as channels_count, SUM(subscribers_count) as total_subscribers
FROM channels 
WHERE subscribers_count > 1000
GROUP BY theme 
ORDER BY total_subscribers DESC;
"""

MOST_CONNECTED_CHANNELS_QUERY = """
SELECT c.id, c.name, c.username, COUNT(cc.id) as connections_count
FROM channels c
LEFT JOIN channel_connections cc ON (c.id = cc.source_id OR c.id = cc.target_id)
WHERE cc.strength > 0.5
GROUP BY c.id, c.name, c.username
ORDER BY connections_count DESC
LIMIT 20;
"""

DUPLICATE_CONTENT_STATS_QUERY = """
SELECT 
    c.theme,
    COUNT(DISTINCT pd.original_post_id) as posts_with_duplicates,
    COUNT(pd.id) as total_duplicates,
    AVG(pd.overall_similarity) as avg_similarity
FROM post_duplicates pd
JOIN posts p ON pd.original_post_id = p.id
JOIN channels c ON p.channel_id = c.id
WHERE pd.overall_similarity > 0.7
GROUP BY c.theme
ORDER BY total_duplicates DESC;
"""

if __name__ == "__main__":
    # Создание таблиц при запуске модуля
    create_tables()
    print("Database tables created successfully!")
