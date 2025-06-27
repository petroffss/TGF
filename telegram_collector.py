# telegram_collector.py - Модуль сбора данных из Telegram API
import asyncio
import logging
import hashlib
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import aiofiles
import aiohttp
from PIL import Image
import imagehash

try:
    from telethon import TelegramClient, events
    from telethon.tl.types import Channel, Chat, User, MessageMediaPhoto, MessageMediaDocument
    from telethon.errors import FloodWaitError, ChannelPrivateError, UsernameNotOccupiedError
except ImportError:
    print("Telethon не установлен. Установите: pip install telethon")

# Конфигурация
@dataclass
class TelegramConfig:
    api_id: str
    api_hash: str
    session_name: str = "telegram_analyzer"
    max_retries: int = 3
    rate_limit_delay: int = 1  # секунды между запросами
    batch_size: int = 100

class TelegramDataCollector:
    """Основной класс для сбора данных из Telegram"""
    
    def __init__(self, config: TelegramConfig):
        self.config = config
        self.client = None
        self.session_active = False
        self.rate_limiter = RateLimiter(delay=config.rate_limit_delay)
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Инициализация клиента Telegram"""
        try:
            self.client = TelegramClient(
                self.config.session_name,
                self.config.api_id,
                self.config.api_hash
            )
            
            await self.client.start()
            self.session_active = True
            self.logger.info("Telegram client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Telegram client: {e}")
            raise
    
    async def disconnect(self):
        """Отключение от Telegram"""
        if self.client and self.session_active:
            await self.client.disconnect()
            self.session_active = False
            self.logger.info("Telegram client disconnected")
    
    async def get_channel_info(self, username: str) -> Optional[Dict]:
        """Получение информации о канале"""
        await self.rate_limiter.wait()
        
        try:
            entity = await self.client.get_entity(username)
            
            if not hasattr(entity, 'broadcast') or not entity.broadcast:
                self.logger.warning(f"{username} is not a channel")
                return None
            
            # Получаем полную информацию о канале
            full_info = await self.client.get_entity(entity)
            
            return {
                'telegram_id': str(entity.id),
                'username': entity.username or username,
                'name': entity.title,
                'description': getattr(entity, 'about', '') or '',
                'subscribers_count': getattr(entity, 'participants_count', 0),
                'verified': getattr(entity, 'verified', False),
                'restricted': getattr(entity, 'restricted', False),
                'scam': getattr(entity, 'scam', False),
                'fake': getattr(entity, 'fake', False),
                'created_date': getattr(entity, 'date', None),
                'metadata': {
                    'access_hash': str(entity.access_hash),
                    'restriction_reason': getattr(entity, 'restriction_reason', None),
                    'username_editable': getattr(entity, 'username', None) is not None
                }
            }
            
        except (ChannelPrivateError, UsernameNotOccupiedError) as e:
            self.logger.warning(f"Channel {username} not accessible: {e}")
            return None
        except FloodWaitError as e:
            self.logger.warning(f"Rate limit hit, waiting {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
            return await self.get_channel_info(username)  # Повторяем запрос
        except Exception as e:
            self.logger.error(f"Error getting channel info for {username}: {e}")
            return None
    
    async def get_channel_posts(self, channel_entity, limit: int = 1000, 
                              offset_date: Optional[datetime] = None) -> List[Dict]:
        """Получение постов канала"""
        posts = []
        
        try:
            async for message in self.client.iter_messages(
                channel_entity, 
                limit=limit,
                offset_date=offset_date
            ):
                await self.rate_limiter.wait()
                
                post_data = await self._process_message(message)
                if post_data:
                    posts.append(post_data)
                
                # Обработка по батчам для снижения нагрузки
                if len(posts) % self.config.batch_size == 0:
                    await asyncio.sleep(1)
            
            self.logger.info(f"Collected {len(posts)} posts from {channel_entity.username}")
            return posts
            
        except FloodWaitError as e:
            self.logger.warning(f"Rate limit hit, waiting {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
            return await self.get_channel_posts(channel_entity, limit, offset_date)
        except Exception as e:
            self.logger.error(f"Error collecting posts: {e}")
            return posts
    
    async def _process_message(self, message) -> Optional[Dict]:
        """Обработка отдельного сообщения"""
        if not message or not message.text:
            return None
        
        # Извлекаем текст и метаданные
        text = message.text or ""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Извлекаем хештеги, упоминания и ссылки
        hashtags = re.findall(r'#\w+', text)
        mentions = re.findall(r'@\w+', text)
        links = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        
        # Обработка медиа
        media_info = await self._process_media(message)
        
        return {
            'telegram_id': str(message.id),
            'text': text,
            'text_hash': text_hash,
            'views': getattr(message, 'views', 0),
            'reactions_count': self._count_reactions(message),
            'replies_count': getattr(message, 'replies', {}).get('replies', 0) if hasattr(message, 'replies') else 0,
            'forwards_count': getattr(message, 'forwards', 0),
            'published_at': message.date,
            'has_media': media_info['has_media'],
            'media_type': media_info['media_type'],
            'media_hash': media_info['media_hash'],
            'hashtags': hashtags,
            'mentions': mentions,
            'links': links,
            'metadata': {
                'message_id': message.id,
                'edit_date': getattr(message, 'edit_date', None),
                'pinned': getattr(message, 'pinned', False),
                'silent': getattr(message, 'silent', False),
                'post_author': getattr(message, 'post_author', None),
                'grouped_id': getattr(message, 'grouped_id', None)
            }
        }
    
    async def _process_media(self, message) -> Dict:
        """Обработка медиафайлов сообщения"""
        if not message.media:
            return {'has_media': False, 'media_type': None, 'media_hash': None}
        
        media_type = type(message.media).__name__
        media_hash = None
        
        try:
            if isinstance(message.media, MessageMediaPhoto):
                media_type = 'photo'
                # Для фото можем вычислить перцептуальный хеш
                photo_path = await self.client.download_media(message.media, file="temp_photo")
                if photo_path:
                    media_hash = await self._calculate_image_hash(photo_path)
                    # Удаляем временный файл
                    import os
                    os.remove(photo_path)
            
            elif isinstance(message.media, MessageMediaDocument):
                media_type = 'document'
                # Для документов используем хеш метаданных
                doc = message.media.document
                media_hash = hashlib.md5(f"{doc.id}_{doc.size}_{doc.mime_type}".encode()).hexdigest()
            
        except Exception as e:
            self.logger.warning(f"Error processing media: {e}")
        
        return {
            'has_media': True,
            'media_type': media_type,
            'media_hash': media_hash
        }
    
    async def _calculate_image_hash(self, image_path: str) -> str:
        """Вычисление перцептуального хеша изображения"""
        try:
            image = Image.open(image_path)
            # Используем дифференциальный хеш для устойчивости к изменениям
            hash_value = str(imagehash.dhash(image))
            return hash_value
        except Exception as e:
            self.logger.warning(f"Error calculating image hash: {e}")
            return None
    
    def _count_reactions(self, message) -> int:
        """Подсчет реакций на сообщение"""
        if not hasattr(message, 'reactions') or not message.reactions:
            return 0
        
        total_reactions = 0
        for reaction in message.reactions.results:
            total_reactions += reaction.count
        
        return total_reactions
    
    async def get_channel_members_sample(self, channel_entity, limit: int = 1000) -> List[Dict]:
        """Получение выборки участников канала (если доступно)"""
        members = []
        
        try:
            async for user in self.client.iter_participants(channel_entity, limit=limit):
                await self.rate_limiter.wait()
                
                member_data = {
                    'user_id': user.id,
                    'username': getattr(user, 'username', None),
                    'first_name': getattr(user, 'first_name', ''),
                    'last_name': getattr(user, 'last_name', ''),
                    'is_bot': getattr(user, 'bot', False),
                    'is_premium': getattr(user, 'premium', False),
                    'is_verified': getattr(user, 'verified', False),
                    'joined_date': getattr(user, 'date', None)
                }
                members.append(member_data)
            
            return members
            
        except Exception as e:
            self.logger.warning(f"Cannot access channel members: {e}")
            return []
    
    async def search_channels_by_keywords(self, keywords: List[str], limit: int = 50) -> List[Dict]:
        """Поиск каналов по ключевым словам"""
        found_channels = []
        
        for keyword in keywords:
            try:
                await self.rate_limiter.wait()
                
                # Поиск через Telegram
                results = await self.client.get_dialogs(limit=limit)
                
                for dialog in results:
                    if hasattr(dialog.entity, 'broadcast') and dialog.entity.broadcast:
                        if keyword.lower() in (dialog.entity.title or "").lower():
                            channel_info = await self.get_channel_info(dialog.entity.username)
                            if channel_info:
                                found_channels.append(channel_info)
                
            except Exception as e:
                self.logger.error(f"Error searching for keyword '{keyword}': {e}")
        
        # Удаляем дубликаты
        unique_channels = []
        seen_ids = set()
        for channel in found_channels:
            if channel['telegram_id'] not in seen_ids:
                unique_channels.append(channel)
                seen_ids.add(channel['telegram_id'])
        
        return unique_channels
    
    async def monitor_channel_updates(self, channel_entities: List, callback):
        """Мониторинг обновлений каналов в реальном времени"""
        @self.client.on(events.NewMessage(chats=channel_entities))
        async def handler(event):
            post_data = await self._process_message(event.message)
            if post_data:
                await callback(event.chat_id, post_data)
        
        self.logger.info(f"Started monitoring {len(channel_entities)} channels")
        await self.client.run_until_disconnected()

class RateLimiter:
    """Класс для ограничения частоты запросов"""
    
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.last_request = 0
    
    async def wait(self):
        """Ожидание перед следующим запросом"""
        now = asyncio.get_event_loop().time()
        time_passed = now - self.last_request
        
        if time_passed < self.delay:
            await asyncio.sleep(self.delay - time_passed)
        
        self.last_request = asyncio.get_event_loop().time()

class BatchProcessor:
    """Класс для батчевой обработки данных"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.current_batch = []
        self.processed_count = 0
    
    async def add_item(self, item, processor_func):
        """Добавление элемента в батч"""
        self.current_batch.append(item)
        
        if len(self.current_batch) >= self.batch_size:
            await self.flush_batch(processor_func)
    
    async def flush_batch(self, processor_func):
        """Обработка текущего батча"""
        if self.current_batch:
            await processor_func(self.current_batch)
            self.processed_count += len(self.current_batch)
            self.current_batch = []

class TelegramAnalyticsCollector:
    """Расширенный коллектор для аналитических данных"""
    
    def __init__(self, base_collector: TelegramDataCollector):
        self.collector = base_collector
        self.logger = logging.getLogger(__name__)
    
    async def collect_cross_posting_evidence(self, channels: List[str], 
                                           time_window_hours: int = 24) -> List[Dict]:
        """Сбор доказательств кросс-постинга между каналами"""
        evidence = []
        cutoff_date = datetime.now() - timedelta(hours=time_window_hours)
        
        # Собираем посты из всех каналов
        all_posts = {}
        for channel_username in channels:
            try:
                entity = await self.collector.client.get_entity(channel_username)
                posts = await self.collector.get_channel_posts(entity, limit=500, offset_date=cutoff_date)
                all_posts[channel_username] = posts
            except Exception as e:
                self.logger.error(f"Error collecting posts from {channel_username}: {e}")
                continue
        
        # Ищем дубликаты между каналами
        for channel1, posts1 in all_posts.items():
            for channel2, posts2 in all_posts.items():
                if channel1 >= channel2:  # Избегаем дублирования пар
                    continue
                
                for post1 in posts1:
                    for post2 in posts2:
                        similarity = self._calculate_post_similarity(post1, post2)
                        
                        if similarity > 0.8:  # Высокая схожесть
                            time_diff = abs((post1['published_at'] - post2['published_at']).total_seconds() / 60)
                            
                            evidence.append({
                                'channel1': channel1,
                                'channel2': channel2,
                                'post1_id': post1['telegram_id'],
                                'post2_id': post2['telegram_id'],
                                'similarity': similarity,
                                'time_diff_minutes': time_diff,
                                'post1_date': post1['published_at'],
                                'post2_date': post2['published_at'],
                                'evidence_type': 'cross_posting'
                            })
        
        return evidence
    
    def _calculate_post_similarity(self, post1: Dict, post2: Dict) -> float:
        """Вычисление схожести постов"""
        text_sim = self._text_similarity(post1.get('text', ''), post2.get('text', ''))
        media_sim = 1.0 if (post1.get('media_hash') and 
                           post1['media_hash'] == post2.get('media_hash')) else 0.0
        
        # Взвешенная схожесть
        if post1.get('has_media') and post2.get('has_media'):
            return 0.7 * text_sim + 0.3 * media_sim
        else:
            return text_sim
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Простая схожесть текстов (можно заменить на более сложные алгоритмы)"""
        if not text1 or not text2:
            return 0.0
        
        # Нормализация текста
        text1 = re.sub(r'\s+', ' ', text1.lower().strip())
        text2 = re.sub(r'\s+', ' ', text2.lower().strip())
        
        # Точное совпадение
        if text1 == text2:
            return 1.0
        
        # Схожесть по словам
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union
    
    async def collect_admin_overlap_data(self, channels: List[str]) -> Dict:
        """Сбор данных о пересечении администраторов"""
        admin_data = {}
        
        for channel_username in channels:
            try:
                entity = await self.collector.client.get_entity(channel_username)
                
                # Получаем список администраторов
                admins = []
                async for admin in self.collector.client.iter_participants(entity, filter='admin'):
                    admins.append({
                        'user_id': admin.id,
                        'username': getattr(admin, 'username', None),
                        'first_name': getattr(admin, 'first_name', ''),
                        'last_name': getattr(admin, 'last_name', '')
                    })
                
                admin_data[channel_username] = admins
                
            except Exception as e:
                self.logger.warning(f"Cannot get admins for {channel_username}: {e}")
                admin_data[channel_username] = []
        
        return admin_data

# Пример использования
async def main():
    # Конфигурация
    config = TelegramConfig(
        api_id="YOUR_API_ID",
        api_hash="YOUR_API_HASH",
        session_name="analyzer_session"
    )
    
    # Создание коллектора
    collector = TelegramDataCollector(config)
    
    try:
        # Инициализация
        await collector.initialize()
        
        # Пример сбора данных о канале
        channel_info = await collector.get_channel_info("@example_channel")
        if channel_info:
            print(f"Channel info: {channel_info}")
            
            # Получение постов
            entity = await collector.client.get_entity("@example_channel")
            posts = await collector.get_channel_posts(entity, limit=100)
            print(f"Collected {len(posts)} posts")
        
        # Пример поиска каналов
        found_channels = await collector.search_channels_by_keywords(["news", "tech"], limit=10)
        print(f"Found {len(found_channels)} channels")
        
    finally:
        await collector.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
