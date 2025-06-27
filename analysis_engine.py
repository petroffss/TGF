# analysis_engine.py - Модуль анализа взаимосвязей каналов
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import LatentDirichletAllocation
import networkx as nx
from scipy import stats
from datetime import datetime, timedelta
import re
import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib

# Попытка импорта дополнительных библиотек
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("spaCy не установлен. Некоторые функции анализа будут недоступны.")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("sentence-transformers не установлен. Семантический анализ будет упрощенным.")

@dataclass
class AnalysisConfig:
    """Конфигурация для модуля анализа"""
    content_similarity_threshold: float = 0.7
    time_correlation_threshold: float = 0.6
    duplicate_threshold: float = 0.85
    network_analysis_depth: int = 3
    min_posts_for_analysis: int = 10
    time_window_hours: int = 24
    semantic_model: str = "all-MiniLM-L6-v2"
    clustering_eps: float = 0.3
    clustering_min_samples: int = 3

class ContentAnalyzer:
    """Анализатор контента для выявления схожести и дубликатов"""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Инициализация моделей
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',  # Можно добавить русские стоп-слова
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95
        )
        
        # Семантическая модель
        self.semantic_model = None
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.semantic_model = SentenceTransformer(config.semantic_model)
                self.logger.info("Semantic model loaded successfully")
            except Exception as e:
                self.logger.warning(f"Failed to load semantic model: {e}")
        
        # Модель spaCy для NLP
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("ru_core_news_sm")  # Для русского языка
            except OSError:
                try:
                    self.nlp = spacy.load("en_core_web_sm")  # Для английского
                except OSError:
                    self.logger.warning("spaCy models not found")
    
    def calculate_text_similarity(self, text1: str, text2: str) -> Dict[str, float]:
        """Вычисление различных метрик схожести текста"""
        if not text1 or not text2:
            return {'tfidf': 0.0, 'semantic': 0.0, 'lexical': 0.0, 'overall': 0.0}
        
        # Нормализация текстов
        text1_clean = self._clean_text(text1)
        text2_clean = self._clean_text(text2)
        
        # TF-IDF схожесть
        tfidf_sim = self._calculate_tfidf_similarity(text1_clean, text2_clean)
        
        # Семантическая схожесть
        semantic_sim = self._calculate_semantic_similarity(text1_clean, text2_clean)
        
        # Лексическая схожесть (пересечение слов)
        lexical_sim = self._calculate_lexical_similarity(text1_clean, text2_clean)
        
        # Общая схожесть (взвешенная)
        overall_sim = (0.4 * tfidf_sim + 0.4 * semantic_sim + 0.2 * lexical_sim)
        
        return {
            'tfidf': tfidf_sim,
            'semantic': semantic_sim,
            'lexical': lexical_sim,
            'overall': overall_sim
        }
    
    def _clean_text(self, text: str) -> str:
        """Очистка и нормализация текста"""
        # Удаление URL
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Удаление mentions и hashtags
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#\w+', '', text)
        
        # Удаление лишних пробелов и символов
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s]', ' ', text)
        
        return text.lower().strip()
    
    def _calculate_tfidf_similarity(self, text1: str, text2: str) -> float:
        """Вычисление TF-IDF схожести"""
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            self.logger.warning(f"TF-IDF calculation failed: {e}")
            return 0.0
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Вычисление семантической схожести"""
        if not self.semantic_model:
            return 0.0
        
        try:
            embeddings = self.semantic_model.encode([text1, text2])
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(similarity)
        except Exception as e:
            self.logger.warning(f"Semantic similarity calculation failed: {e}")
            return 0.0
    
    def _calculate_lexical_similarity(self, text1: str, text2: str) -> float:
        """Вычисление лексической схожести"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def detect_duplicates(self, posts: List[Dict]) -> List[Dict]:
        """Обнаружение дубликатов в списке постов"""
        duplicates = []
        
        for i, post1 in enumerate(posts):
            for j, post2 in enumerate(posts[i+1:], i+1):
                similarity = self.calculate_text_similarity(
                    post1.get('text', ''), 
                    post2.get('text', '')
                )
                
                if similarity['overall'] > self.config.duplicate_threshold:
                    duplicates.append({
                        'post1_id': post1.get('id', post1.get('telegram_id')),
                        'post2_id': post2.get('id', post2.get('telegram_id')),
                        'similarity_metrics': similarity,
                        'time_diff_minutes': self._calculate_time_diff(
                            post1.get('published_at'), 
                            post2.get('published_at')
                        ),
                        'duplicate_type': self._classify_duplicate_type(similarity)
                    })
        
        return duplicates
    
    def _calculate_time_diff(self, date1, date2) -> float:
        """Вычисление разности времени в минутах"""
        if not date1 or not date2:
            return 0.0
        
        if isinstance(date1, str):
            date1 = datetime.fromisoformat(date1.replace('Z', '+00:00'))
        if isinstance(date2, str):
            date2 = datetime.fromisoformat(date2.replace('Z', '+00:00'))
        
        return abs((date1 - date2).total_seconds() / 60)
    
    def _classify_duplicate_type(self, similarity: Dict[str, float]) -> str:
        """Классификация типа дубликата"""
        if similarity['overall'] > 0.95:
            return 'exact'
        elif similarity['semantic'] > 0.8:
            return 'semantic'
        elif similarity['tfidf'] > 0.8:
            return 'textual'
        else:
            return 'partial'
    
    def extract_topics(self, texts: List[str], n_topics: int = 10) -> Dict:
        """Извлечение тем из текстов с помощью LDA"""
        try:
            # Подготовка данных
            clean_texts = [self._clean_text(text) for text in texts if text]
            
            if len(clean_texts) < n_topics:
                return {'topics': [], 'topic_distribution': []}
            
            # Векторизация
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(clean_texts)
            
            # LDA модель
            lda = LatentDirichletAllocation(
                n_components=n_topics,
                random_state=42,
                max_iter=100
            )
            
            lda.fit(tfidf_matrix)
            topic_distribution = lda.transform(tfidf_matrix)
            
            # Извлечение ключевых слов для каждой темы
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            topics = []
            
            for topic_idx, topic in enumerate(lda.components_):
                top_words_idx = topic.argsort()[-10:][::-1]
                top_words = [feature_names[i] for i in top_words_idx]
                topics.append({
                    'id': topic_idx,
                    'keywords': top_words,
                    'weight': float(topic.sum())
                })
            
            return {
                'topics': topics,
                'topic_distribution': topic_distribution.tolist()
            }
            
        except Exception as e:
            self.logger.error(f"Topic extraction failed: {e}")
            return {'topics': [], 'topic_distribution': []}

class TemporalAnalyzer:
    """Анализатор временных паттернов"""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def calculate_time_correlation(self, posts1: List[Dict], posts2: List[Dict]) -> Dict:
        """Вычисление временной корреляции между каналами"""
        # Группировка постов по часам
        hourly_activity1 = self._get_hourly_activity(posts1)
        hourly_activity2 = self._get_hourly_activity(posts2)
        
        # Вычисление корреляции Пирсона
        hours = range(24)
        activity1 = [hourly_activity1.get(h, 0) for h in hours]
        activity2 = [hourly_activity2.get(h, 0) for h in hours]
        
        correlation, p_value = stats.pearsonr(activity1, activity2)
        
        # Анализ синхронных публикаций
        sync_posts = self._find_synchronized_posts(posts1, posts2)
        
        # Анализ последовательности публикаций
        sequence_analysis = self._analyze_posting_sequence(posts1, posts2)
        
        return {
            'hourly_correlation': float(correlation) if not np.isnan(correlation) else 0.0,
            'correlation_p_value': float(p_value) if not np.isnan(p_value) else 1.0,
            'synchronized_posts': len(sync_posts),
            'sync_details': sync_posts[:10],  # Первые 10 примеров
            'sequence_analysis': sequence_analysis,
            'activity_patterns': {
                'channel1_peak_hours': self._find_peak_hours(hourly_activity1),
                'channel2_peak_hours': self._find_peak_hours(hourly_activity2)
            }
        }
    
    def _get_hourly_activity(self, posts: List[Dict]) -> Dict[int, int]:
        """Получение активности по часам"""
        hourly_activity = {}
        
        for post in posts:
            published_at = post.get('published_at')
            if published_at:
                if isinstance(published_at, str):
                    published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                
                hour = published_at.hour
                hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
        
        return hourly_activity
    
    def _find_synchronized_posts(self, posts1: List[Dict], posts2: List[Dict]) -> List[Dict]:
        """Поиск синхронных публикаций"""
        sync_posts = []
        threshold_minutes = 30
        
        for post1 in posts1:
            for post2 in posts2:
                time_diff = self._calculate_time_diff(
                    post1.get('published_at'),
                    post2.get('published_at')
                )
                
                if time_diff <= threshold_minutes:
                    sync_posts.append({
                        'post1_id': post1.get('id', post1.get('telegram_id')),
                        'post2_id': post2.get('id', post2.get('telegram_id')),
                        'time_diff_minutes': time_diff,
                        'post1_date': post1.get('published_at'),
                        'post2_date': post2.get('published_at')
                    })
        
        return sorted(sync_posts, key=lambda x: x['time_diff_minutes'])
    
    def _analyze_posting_sequence(self, posts1: List[Dict], posts2: List[Dict]) -> Dict:
        """Анализ последовательности публикаций"""
        # Определяем, кто публикует первым
        lead_lag_analysis = []
        
        for post1 in posts1:
            closest_post2 = None
            min_time_diff = float('inf')
            
            for post2 in posts2:
                time_diff = self._calculate_time_diff_signed(
                    post1.get('published_at'),
                    post2.get('published_at')
                )
                
                if abs(time_diff) < min_time_diff and abs(time_diff) <= 120:  # В пределах 2 часов
                    min_time_diff = abs(time_diff)
                    closest_post2 = post2
                    lead_lag_time = time_diff
            
            if closest_post2:
                lead_lag_analysis.append({
                    'time_diff': lead_lag_time,
                    'channel1_leads': lead_lag_time < 0
                })
        
        if lead_lag_analysis:
            channel1_leads_count = sum(1 for x in lead_lag_analysis if x['channel1_leads'])
            avg_lead_time = np.mean([abs(x['time_diff']) for x in lead_lag_analysis])
            
            return {
                'total_pairs': len(lead_lag_analysis),
                'channel1_leads_count': channel1_leads_count,
                'channel2_leads_count': len(lead_lag_analysis) - channel1_leads_count,
                'average_lead_time_minutes': float(avg_lead_time),
                'dominant_leader': 'channel1' if channel1_leads_count > len(lead_lag_analysis) / 2 else 'channel2'
            }
        
        return {'total_pairs': 0}
    
    def _calculate_time_diff_signed(self, date1, date2) -> float:
        """Вычисление знаковой разности времени (date1 - date2) в минутах"""
        if not date1 or not date2:
            return 0.0
        
        if isinstance(date1, str):
            date1 = datetime.fromisoformat(date1.replace('Z', '+00:00'))
        if isinstance(date2, str):
            date2 = datetime.fromisoformat(date2.replace('Z', '+00:00'))
        
        return (date1 - date2).total_seconds() / 60
    
    def _calculate_time_diff(self, date1, date2) -> float:
        """Вычисление абсолютной разности времени в минутах"""
        return abs(self._calculate_time_diff_signed(date1, date2))
    
    def _find_peak_hours(self, hourly_activity: Dict[int, int], top_k: int = 3) -> List[int]:
        """Поиск часов пиковой активности"""
        sorted_hours = sorted(hourly_activity.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, _ in sorted_hours[:top_k]]

class NetworkAnalyzer:
    """Анализатор сетевых структур"""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def build_channel_network(self, connections: List[Dict]) -> nx.Graph:
        """Построение графа каналов"""
        G = nx.Graph()
        
        for conn in connections:
            source_id = conn.get('source_id')
            target_id = conn.get('target_id')
            strength = conn.get('strength', 0.0)
            connection_type = conn.get('connection_type', 'unknown')
            
            if source_id and target_id:
                G.add_edge(
                    source_id, 
                    target_id, 
                    weight=strength,
                    connection_type=connection_type,
                    **conn
                )
        
        return G
    
    def calculate_network_metrics(self, graph: nx.Graph, channel_id: int) -> Dict:
        """Вычисление сетевых метрик для канала"""
        if channel_id not in graph.nodes():
            return self._empty_metrics()
        
        metrics = {}
        
        try:
            # Базовые метрики
            metrics['degree'] = graph.degree(channel_id)
            metrics['weighted_degree'] = graph.degree(channel_id, weight='weight')
            
            # Метрики центральности
            if len(graph.nodes()) > 1:
                centrality_metrics = self._calculate_centrality_metrics(graph, channel_id)
                metrics.update(centrality_metrics)
            
            # Метрики кластеризации
            metrics['clustering_coefficient'] = nx.clustering(graph, channel_id)
            
            # Локальные метрики
            neighbors = list(graph.neighbors(channel_id))
            metrics['neighbors_count'] = len(neighbors)
            metrics['neighbors'] = neighbors
            
            # Метрики связей
            edge_metrics = self._analyze_edge_types(graph, channel_id)
            metrics.update(edge_metrics)
            
        except Exception as e:
            self.logger.error(f"Error calculating network metrics: {e}")
            return self._empty_metrics()
        
        return metrics
    
    def _calculate_centrality_metrics(self, graph: nx.Graph, channel_id: int) -> Dict:
        """Вычисление метрик центральности"""
        metrics = {}
        
        try:
            # Degree centrality
            degree_centrality = nx.degree_centrality(graph)
            metrics['degree_centrality'] = degree_centrality.get(channel_id, 0.0)
            
            # Betweenness centrality
            betweenness_centrality = nx.betweenness_centrality(graph, weight='weight')
            metrics['betweenness_centrality'] = betweenness_centrality.get(channel_id, 0.0)
            
            # Closeness centrality
            if nx.is_connected(graph):
                closeness_centrality = nx.closeness_centrality(graph, distance='weight')
                metrics['closeness_centrality'] = closeness_centrality.get(channel_id, 0.0)
            else:
                metrics['closeness_centrality'] = 0.0
            
            # Eigenvector centrality
            try:
                eigenvector_centrality = nx.eigenvector_centrality(graph, weight='weight')
                metrics['eigenvector_centrality'] = eigenvector_centrality.get(channel_id, 0.0)
            except:
                metrics['eigenvector_centrality'] = 0.0
            
            # PageRank
            pagerank = nx.pagerank(graph, weight='weight')
            metrics['pagerank'] = pagerank.get(channel_id, 0.0)
            
        except Exception as e:
            self.logger.warning(f"Error calculating centrality metrics: {e}")
            metrics.update({
                'degree_centrality': 0.0,
                'betweenness_centrality': 0.0,
                'closeness_centrality': 0.0,
                'eigenvector_centrality': 0.0,
                'pagerank': 0.0
            })
        
        return metrics
    
    def _analyze_edge_types(self, graph: nx.Graph, channel_id: int) -> Dict:
        """Анализ типов связей"""
        edge_types = {}
        strong_connections = 0
        
        for neighbor in graph.neighbors(channel_id):
            edge_data = graph[channel_id][neighbor]
            connection_type = edge_data.get('connection_type', 'unknown')
            strength = edge_data.get('weight', 0.0)
            
            edge_types[connection_type] = edge_types.get(connection_type, 0) + 1
            
            if strength > 0.7:
                strong_connections += 1
        
        return {
            'connection_types': edge_types,
            'strong_connections': strong_connections,
            'total_connections': len(list(graph.neighbors(channel_id)))
        }
    
    def _empty_metrics(self) -> Dict:
        """Пустые метрики для каналов без связей"""
        return {
            'degree': 0,
            'weighted_degree': 0.0,
            'degree_centrality': 0.0,
            'betweenness_centrality': 0.0,
            'closeness_centrality': 0.0,
            'eigenvector_centrality': 0.0,
            'pagerank': 0.0,
            'clustering_coefficient': 0.0,
            'neighbors_count': 0,
            'neighbors': [],
            'connection_types': {},
            'strong_connections': 0,
            'total_connections': 0
        }
    
    def detect_communities(self, graph: nx.Graph) -> Dict:
        """Обнаружение сообществ в сети"""
        try:
            # Используем алгоритм Лувена (через приближение с другими методами)
            communities = self._louvain_approximation(graph)
            
            # Метрики сообществ
            modularity = self._calculate_modularity(graph, communities)
            
            # Статистика сообществ
            community_stats = {}
            for community_id, nodes in communities.items():
                subgraph = graph.subgraph(nodes)
                community_stats[community_id] = {
                    'size': len(nodes),
                    'density': nx.density(subgraph),
                    'nodes': list(nodes)
                }
            
            return {
                'communities': communities,
                'modularity': modularity,
                'community_count': len(communities),
                'community_stats': community_stats
            }
            
        except Exception as e:
            self.logger.error(f"Community detection failed: {e}")
            return {'communities': {}, 'modularity': 0.0, 'community_count': 0}
    
    def _louvain_approximation(self, graph: nx.Graph) -> Dict:
        """Приближенная реализация алгоритма Лувена"""
        # Упрощенный алгоритм группировки узлов
        communities = {}
        community_id = 0
        visited = set()
        
        for node in graph.nodes():
            if node not in visited:
                community = self._expand_community(graph, node, visited)
                communities[community_id] = community
                community_id += 1
        
        return communities
    
    def _expand_community(self, graph: nx.Graph, start_node: int, visited: Set) -> Set:
        """Расширение сообщества от начального узла"""
        community = {start_node}
        visited.add(start_node)
        queue = [start_node]
        
        while queue:
            current_node = queue.pop(0)
            
            for neighbor in graph.neighbors(current_node):
                if neighbor not in visited:
                    edge_weight = graph[current_node][neighbor].get('weight', 0.0)
                    
                    if edge_weight > 0.5:  # Порог для включения в сообщество
                        community.add(neighbor)
                        visited.add(neighbor)
                        queue.append(neighbor)
        
        return community
    
    def _calculate_modularity(self, graph: nx.Graph, communities: Dict) -> float:
        """Вычисление модулярности разбиения"""
        try:
            # Создаем список принадлежности узлов к сообществам
            node_to_community = {}
            for community_id, nodes in communities.items():
                for node in nodes:
                    node_to_community[node] = community_id
            
            # Простое вычисление модулярности
            total_edges = graph.number_of_edges()
            if total_edges == 0:
                return 0.0
            
            modularity = 0.0
            for community_id, nodes in communities.items():
                subgraph = graph.subgraph(nodes)
                internal_edges = subgraph.number_of_edges()
                
                # Доля внутренних связей
                if total_edges > 0:
                    modularity += internal_edges / total_edges
            
            return modularity
            
        except Exception:
            return 0.0

class MainAnalysisEngine:
    """Главный движок анализа, объединяющий все анализаторы"""
    
    def __init__(self, config: AnalysisConfig = None):
        self.config = config or AnalysisConfig()
        self.content_analyzer = ContentAnalyzer(self.config)
        self.temporal_analyzer = TemporalAnalyzer(self.config)
        self.network_analyzer = NetworkAnalyzer(self.config)
        self.logger = logging.getLogger(__name__)
        
        # Пул потоков для параллельной обработки
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def analyze_channel_relationships(self, channel_id: int, 
                                          related_channels: List[Dict],
                                          posts: List[Dict]) -> Dict:
        """Комплексный анализ связей канала"""
        analysis_results = {
            'channel_id': channel_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'content_analysis': {},
            'temporal_analysis': {},
            'network_analysis': {},
            'relationship_summary': {}
        }
        
        # Параллельный запуск различных типов анализа
        tasks = []
        
        # Анализ контента
        content_task = asyncio.create_task(
            self._analyze_content_relationships(channel_id, related_channels, posts)
        )
        tasks.append(('content', content_task))
        
        # Временной анализ
        temporal_task = asyncio.create_task(
            self._analyze_temporal_relationships(channel_id, related_channels, posts)
        )
        tasks.append(('temporal', temporal_task))
        
        # Сетевой анализ
        network_task = asyncio.create_task(
            self._analyze_network_relationships(channel_id, related_channels)
        )
        tasks.append(('network', network_task))
        
        # Ожидание завершения всех задач
        for analysis_type, task in tasks:
            try:
                result = await task
                analysis_results[f'{analysis_type}_analysis'] = result
            except Exception as e:
                self.logger.error(f"Error in {analysis_type} analysis: {e}")
                analysis_results[f'{analysis_type}_analysis'] = {}
        
        # Создание сводки по связям
        analysis_results['relationship_summary'] = self._create_relationship_summary(
            analysis_results
        )
        
        return analysis_results
    
    async def _analyze_content_relationships(self, channel_id: int, 
                                           related_channels: List[Dict], 
                                           posts: List[Dict]) -> Dict:
        """Анализ связей по контенту"""
        content_results = {
            'duplicate_analysis': {},
            'similarity_analysis': {},
            'topic_analysis': {},
            'keyword_analysis': {}
        }
        
        # Обнаружение дубликатов
        duplicates = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.content_analyzer.detect_duplicates,
            posts
        )
        content_results['duplicate_analysis'] = {
            'total_duplicates': len(duplicates),
            'duplicates': duplicates[:20],  # Первые 20
            'duplicate_rate': len(duplicates) / len(posts) if posts else 0
        }
        
        # Анализ схожести с другими каналами
        similarity_results = []
        for related_channel in related_channels:
            related_posts = related_channel.get('posts', [])
            if related_posts:
                # Вычисляем среднюю схожесть постов
                similarities = []
                for post in posts[:50]:  # Ограничиваем для производительности
                    for related_post in related_posts[:50]:
                        sim = self.content_analyzer.calculate_text_similarity(
                            post.get('text', ''),
                            related_post.get('text', '')
                        )
                        similarities.append(sim['overall'])
                
                if similarities:
                    avg_similarity = np.mean(similarities)
                    max_similarity = np.max(similarities)
                    
                    similarity_results.append({
                        'channel_id': related_channel.get('id'),
                        'channel_name': related_channel.get('name'),
                        'average_similarity': float(avg_similarity),
                        'max_similarity': float(max_similarity),
                        'high_similarity_count': sum(1 for s in similarities if s > 0.7)
                    })
        
        content_results['similarity_analysis'] = similarity_results
        
        # Анализ тем
        all_texts = [post.get('text', '') for post in posts if post.get('text')]
        if all_texts:
            topics = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.content_analyzer.extract_topics,
                all_texts
            )
            content_results['topic_analysis'] = topics
        
        return content_results
    
    async def _analyze_temporal_relationships(self, channel_id: int,
                                            related_channels: List[Dict],
                                            posts: List[Dict]) -> Dict:
        """Анализ временных связей"""
        temporal_results = {
            'posting_patterns': {},
            'correlations': [],
            'synchronization_analysis': {}
        }
        
        # Анализ паттернов публикации
        hourly_activity = self.temporal_analyzer._get_hourly_activity(posts)
        peak_hours = self.temporal_analyzer._find_peak_hours(hourly_activity)
        
        temporal_results['posting_patterns'] = {
            'hourly_distribution': hourly_activity,
            'peak_hours': peak_hours,
            'total_posts': len(posts),
            'average_posts_per_hour': len(posts) / 24 if posts else 0
        }
        
        # Корреляционный анализ с другими каналами
        for related_channel in related_channels:
            related_posts = related_channel.get('posts', [])
            if related_posts:
                correlation = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self.temporal_analyzer.calculate_time_correlation,
                    posts,
                    related_posts
                )
                
                correlation['related_channel'] = {
                    'id': related_channel.get('id'),
                    'name': related_channel.get('name')
                }
                temporal_results['correlations'].append(correlation)
        
        return temporal_results
    
    async def _analyze_network_relationships(self, channel_id: int,
                                           related_channels: List[Dict]) -> Dict:
        """Анализ сетевых связей"""
        # Создаем граф из связей
        connections = []
        for related_channel in related_channels:
            connection = related_channel.get('connection', {})
            if connection:
                connections.append({
                    'source_id': channel_id,
                    'target_id': related_channel.get('id'),
                    'strength': connection.get('strength', 0.0),
                    'connection_type': connection.get('type', 'unknown')
                })
        
        if not connections:
            return {'metrics': self.network_analyzer._empty_metrics()}
        
        # Строим граф
        graph = self.network_analyzer.build_channel_network(connections)
        
        # Вычисляем метрики
        metrics = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.network_analyzer.calculate_network_metrics,
            graph,
            channel_id
        )
        
        # Обнаружение сообществ
        communities = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.network_analyzer.detect_communities,
            graph
        )
        
        return {
            'metrics': metrics,
            'communities': communities,
            'graph_stats': {
                'nodes_count': graph.number_of_nodes(),
                'edges_count': graph.number_of_edges(),
                'density': nx.density(graph),
                'is_connected': nx.is_connected(graph)
            }
        }
    
    def _create_relationship_summary(self, analysis_results: Dict) -> Dict:
        """Создание сводки по выявленным связям"""
        summary = {
            'total_connections': 0,
            'strong_connections': 0,
            'connection_types': {},
            'confidence_score': 0.0,
            'key_insights': []
        }
        
        # Анализируем результаты контентного анализа
        content = analysis_results.get('content_analysis', {})
        duplicate_rate = content.get('duplicate_analysis', {}).get('duplicate_rate', 0)
        
        if duplicate_rate > 0.1:
            summary['key_insights'].append(f"Высокий уровень дубликатов контента: {duplicate_rate:.1%}")
        
        # Анализируем временные корреляции
        temporal = analysis_results.get('temporal_analysis', {})
        correlations = temporal.get('correlations', [])
        
        strong_time_correlations = [c for c in correlations 
                                  if c.get('hourly_correlation', 0) > 0.6]
        
        if strong_time_correlations:
            summary['key_insights'].append(f"Обнаружено {len(strong_time_correlations)} сильных временных корреляций")
        
        # Анализируем сетевые метрики
        network = analysis_results.get('network_analysis', {})
        metrics = network.get('metrics', {})
        
        summary['total_connections'] = metrics.get('total_connections', 0)
        summary['strong_connections'] = metrics.get('strong_connections', 0)
        summary['connection_types'] = metrics.get('connection_types', {})
        
        # Вычисляем общий скор уверенности
        confidence_factors = []
        
        if duplicate_rate > 0:
            confidence_factors.append(min(duplicate_rate * 2, 1.0))
        
        if strong_time_correlations:
            avg_correlation = np.mean([c.get('hourly_correlation', 0) for c in strong_time_correlations])
            confidence_factors.append(avg_correlation)
        
        if metrics.get('pagerank', 0) > 0:
            confidence_factors.append(min(metrics['pagerank'] * 10, 1.0))
        
        summary['confidence_score'] = float(np.mean(confidence_factors)) if confidence_factors else 0.0
        
        return summary

# Пример использования
async def main():
    # Конфигурация
    config = AnalysisConfig(
        content_similarity_threshold=0.7,
        time_correlation_threshold=0.6,
        duplicate_threshold=0.85
    )
    
    # Создание анализатора
    analyzer = MainAnalysisEngine(config)
    
    # Пример данных
    posts = [
        {
            'id': 1,
            'text': 'Пример текста поста',
            'published_at': datetime.now(),
            'views': 1000
        }
    ]
    
    related_channels = [
        {
            'id': 2,
            'name': 'Related Channel',
            'posts': posts,
            'connection': {'strength': 0.8, 'type': 'content_similarity'}
        }
    ]
    
    # Выполнение анализа
    results = await analyzer.analyze_channel_relationships(1, related_channels, posts)
    
    print("Результаты анализа:")
    print(f"Confidence Score: {results['relationship_summary']['confidence_score']:.2f}")
    print(f"Key Insights: {results['relationship_summary']['key_insights']}")

if __name__ == "__main__":
    asyncio.run(main())
