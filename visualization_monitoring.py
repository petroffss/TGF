# visualization_monitoring.py - Модуль визуализации и мониторинга
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aioredis
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
import pandas as pd
import numpy as np
from dataclasses import dataclass
from pathlib import Path

# Конфигурация для мониторинга
@dataclass
class MonitoringConfig:
    redis_url: str = "redis://localhost:6379"
    alert_email: str = "admin@example.com"
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    check_interval_minutes: int = 30
    thresholds: Dict = None
    
    def __post_init__(self):
        if self.thresholds is None:
            self.thresholds = {
                'high_similarity_threshold': 0.85,
                'suspicious_sync_threshold': 10,  # синхронных постов
                'rapid_growth_threshold': 0.2,   # 20% рост за день
                'duplicate_rate_threshold': 0.3  # 30% дубликатов
            }

class NetworkVisualizer:
    """Класс для создания интерактивных визуализаций сетей"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_network_graph(self, channels: List[Dict], connections: List[Dict], 
                           focus_channel_id: Optional[int] = None) -> Dict:
        """Создание интерактивного графа сети каналов"""
        try:
            # Создаем NetworkX граф
            G = nx.Graph()
            
            # Добавляем узлы (каналы)
            for channel in channels:
                G.add_node(
                    channel['id'],
                    name=channel.get('name', ''),
                    subscribers=channel.get('subscribers_count', 0),
                    theme=channel.get('theme', ''),
                    verified=channel.get('verified', False)
                )
            
            # Добавляем рёбра (связи)
            for conn in connections:
                if conn.get('source_id') and conn.get('target_id'):
                    G.add_edge(
                        conn['source_id'],
                        conn['target_id'],
                        strength=conn.get('strength', 0.0),
                        type=conn.get('connection_type', 'unknown')
                    )
            
            # Вычисляем позиции узлов
            pos = self._calculate_layout(G, focus_channel_id)
            
            # Создаем данные для Plotly
            plotly_data = self._convert_to_plotly(G, pos, focus_channel_id)
            
            return {
                'data': plotly_data,
                'layout': self._create_network_layout(),
                'stats': {
                    'nodes': G.number_of_nodes(),
                    'edges': G.number_of_edges(),
                    'density': nx.density(G),
                    'components': nx.number_connected_components(G)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error creating network graph: {e}")
            return {'data': [], 'layout': {}, 'stats': {}}
    
    def _calculate_layout(self, graph: nx.Graph, focus_id: Optional[int] = None) -> Dict:
        """Вычисление позиций узлов для оптимального отображения"""
        if focus_id and focus_id in graph.nodes():
            # Используем spring layout с фиксированной позицией центрального узла
            fixed_pos = {focus_id: (0, 0)}
            pos = nx.spring_layout(
                graph, 
                pos=fixed_pos, 
                fixed=[focus_id],
                k=3, 
                iterations=50
            )
        else:
            # Обычный spring layout
            pos = nx.spring_layout(graph, k=3, iterations=50)
        
        return pos
    
    def _convert_to_plotly(self, graph: nx.Graph, pos: Dict, focus_id: Optional[int] = None) -> List[Dict]:
        """Конвертация NetworkX графа в формат Plotly"""
        # Создаем линии для рёбер
        edge_x = []
        edge_y = []
        edge_info = []
        
        for edge in graph.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
            strength = edge[2].get('strength', 0.0)
            conn_type = edge[2].get('type', 'unknown')
            edge_info.append(f"Сила связи: {strength:.2f}<br>Тип: {conn_type}")
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Создаем точки для узлов
        node_x = []
        node_y = []
        node_text = []
        node_info = []
        node_colors = []
        node_sizes = []
        
        for node in graph.nodes(data=True):
            x, y = pos[node[0]]
            node_x.append(x)
            node_y.append(y)
            
            name = node[1].get('name', f'Channel {node[0]}')
            subscribers = node[1].get('subscribers', 0)
            theme = node[1].get('theme', 'Unknown')
            verified = node[1].get('verified', False)
            
            node_text.append(name)
            node_info.append(
                f"<b>{name}</b><br>"
                f"ID: {node[0]}<br>"
                f"Подписчики: {subscribers:,}<br>"
                f"Тема: {theme}<br>"
                f"Verified: {'Да' if verified else 'Нет'}<br>"
                f"Связей: {graph.degree(node[0])}"
            )
            
            # Цвет узла
            if node[0] == focus_id:
                node_colors.append('red')
                node_sizes.append(20)
            elif verified:
                node_colors.append('gold')
                node_sizes.append(15)
            else:
                node_colors.append('lightblue')
                node_sizes.append(10)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="middle center",
            hovertext=node_info,
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='white')
            )
        )
        
        return [edge_trace, node_trace]
    
    def _create_network_layout(self) -> Dict:
        """Создание layout для сетевого графа"""
        return dict(
            title="Граф взаимосвязей каналов",
            titlefont_size=16,
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[ dict(
                text="Размер узла зависит от важности канала",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002,
                xanchor='left', yanchor='bottom',
                font=dict(color='gray', size=12)
            )],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            width=800,
            height=600
        )
    
    def create_temporal_heatmap(self, channels_activity: Dict[int, Dict]) -> Dict:
        """Создание тепловой карты активности каналов по времени"""
        try:
            # Подготавливаем данные
            channel_names = []
            hours = list(range(24))
            activity_matrix = []
            
            for channel_id, activity_data in channels_activity.items():
                channel_names.append(activity_data.get('name', f'Channel {channel_id}'))
                hourly_activity = activity_data.get('hourly_activity', {})
                
                # Нормализуем активность для каждого канала
                max_activity = max(hourly_activity.values()) if hourly_activity else 1
                normalized_activity = [
                    hourly_activity.get(hour, 0) / max_activity 
                    for hour in hours
                ]
                activity_matrix.append(normalized_activity)
            
            # Создаем heatmap
            fig = go.Figure(data=go.Heatmap(
                z=activity_matrix,
                x=[f"{h:02d}:00" for h in hours],
                y=channel_names,
                colorscale='Viridis',
                showscale=True,
                hovertemplate='<b>%{y}</b><br>Время: %{x}<br>Активность: %{z:.2f}<extra></extra>'
            ))
            
            fig.update_layout(
                title="Тепловая карта активности каналов по часам",
                xaxis_title="Час дня",
                yaxis_title="Каналы",
                width=800,
                height=max(400, len(channel_names) * 25)
            )
            
            return fig.to_dict()
            
        except Exception as e:
            self.logger.error(f"Error creating temporal heatmap: {e}")
            return {}
    
    def create_similarity_matrix(self, similarity_data: List[Dict]) -> Dict:
        """Создание матрицы схожести каналов"""
        try:
            # Получаем уникальные каналы
            channels = set()
            for item in similarity_data:
                channels.add(item['channel1_id'])
                channels.add(item['channel2_id'])
            
            channels = sorted(list(channels))
            n = len(channels)
            
            # Создаем матрицу схожести
            similarity_matrix = np.zeros((n, n))
            
            for item in similarity_data:
                i = channels.index(item['channel1_id'])
                j = channels.index(item['channel2_id'])
                similarity = item.get('similarity', 0.0)
                
                similarity_matrix[i][j] = similarity
                similarity_matrix[j][i] = similarity  # Симметричная матрица
            
            # Заполняем диагональ единицами
            np.fill_diagonal(similarity_matrix, 1.0)
            
            # Создаем heatmap
            fig = go.Figure(data=go.Heatmap(
                z=similarity_matrix,
                x=[f"Channel {ch}" for ch in channels],
                y=[f"Channel {ch}" for ch in channels],
                colorscale='RdYlBu_r',
                zmin=0,
                zmax=1,
                showscale=True,
                hovertemplate='Канал %{y} ↔ %{x}<br>Схожесть: %{z:.3f}<extra></extra>'
            ))
            
            fig.update_layout(
                title="Матрица схожести каналов",
                width=600,
                height=600
            )
            
            return fig.to_dict()
            
        except Exception as e:
            self.logger.error(f"Error creating similarity matrix: {e}")
            return {}

class DashboardGenerator:
    """Генератор дашбордов для аналитики"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_overview_dashboard(self, stats: Dict) -> Dict:
        """Создание обзорного дашборда"""
        try:
            # Создаем subplot с метриками
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Распределение по темам', 'Рост каналов', 
                              'Активность по часам', 'Топ связанных каналов'),
                specs=[[{"type": "pie"}, {"type": "scatter"}],
                       [{"type": "bar"}, {"type": "bar"}]]
            )
            
            # 1. Круговая диаграмма тем
            themes = stats.get('themes_distribution', {})
            if themes:
                fig.add_trace(
                    go.Pie(labels=list(themes.keys()), values=list(themes.values())),
                    row=1, col=1
                )
            
            # 2. График роста каналов
            growth_data = stats.get('channel_growth', {})
            if growth_data:
                dates = list(growth_data.keys())
                counts = list(growth_data.values())
                fig.add_trace(
                    go.Scatter(x=dates, y=counts, mode='lines+markers', name='Каналы'),
                    row=1, col=2
                )
            
            # 3. Активность по часам
            hourly_stats = stats.get('hourly_activity', {})
            if hourly_stats:
                hours = list(range(24))
                activity = [hourly_stats.get(str(h), 0) for h in hours]
                fig.add_trace(
                    go.Bar(x=hours, y=activity, name='Посты'),
                    row=2, col=1
                )
            
            # 4. Топ связанных каналов
            top_connected = stats.get('top_connected_channels', [])[:10]
            if top_connected:
                names = [ch['name'][:20] for ch in top_connected]
                connections = [ch['connections_count'] for ch in top_connected]
                fig.add_trace(
                    go.Bar(x=connections, y=names, orientation='h', name='Связи'),
                    row=2, col=2
                )
            
            fig.update_layout(
                title_text="Обзорный дашборд системы",
                height=800,
                showlegend=False
            )
            
            return fig.to_dict()
            
        except Exception as e:
            self.logger.error(f"Error creating overview dashboard: {e}")
            return {}
    
    def create_channel_analysis_dashboard(self, channel_data: Dict, analysis_results: Dict) -> Dict:
        """Создание дашборда анализа конкретного канала"""
        try:
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=(
                    'Активность по дням недели', 'Распределение просмотров',
                    'Схожесть с другими каналами', 'Временные корреляции',
                    'Ключевые слова', 'Сетевые метрики'
                ),
                specs=[
                    [{"type": "bar"}, {"type": "histogram"}],
                    [{"type": "bar"}, {"type": "heatmap"}],
                    [{"type": "bar"}, {"type": "bar"}]
                ]
            )
            
            # 1. Активность по дням недели
            weekly_activity = analysis_results.get('temporal_analysis', {}).get('weekly_activity', {})
            if weekly_activity:
                days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
                activity = [weekly_activity.get(str(i), 0) for i in range(7)]
                fig.add_trace(
                    go.Bar(x=days, y=activity, name='Посты'),
                    row=1, col=1
                )
            
            # 2. Распределение просмотров
            posts = channel_data.get('posts', [])
            if posts:
                views = [post.get('views', 0) for post in posts if post.get('views')]
                fig.add_trace(
                    go.Histogram(x=views, nbinsx=20, name='Просмотры'),
                    row=1, col=2
                )
            
            # 3. Схожесть с другими каналами
            similarity_analysis = analysis_results.get('content_analysis', {}).get('similarity_analysis', [])
            if similarity_analysis:
                top_similar = similarity_analysis[:10]
                names = [ch['channel_name'][:15] for ch in top_similar]
                similarities = [ch['average_similarity'] for ch in top_similar]
                fig.add_trace(
                    go.Bar(x=similarities, y=names, orientation='h', name='Схожесть'),
                    row=2, col=1
                )
            
            # 4. Временные корреляции
            correlations = analysis_results.get('temporal_analysis', {}).get('correlations', [])
            if correlations:
                corr_matrix = []
                channel_names = []
                for corr in correlations[:10]:
                    channel_names.append(corr.get('related_channel', {}).get('name', 'Unknown')[:10])
                    corr_matrix.append([corr.get('hourly_correlation', 0)])
                
                fig.add_trace(
                    go.Heatmap(
                        z=corr_matrix,
                        y=channel_names,
                        x=['Корреляция'],
                        colorscale='RdYlBu',
                        showscale=False
                    ),
                    row=2, col=2
                )
            
            # 5. Ключевые слова
            topics = analysis_results.get('content_analysis', {}).get('topic_analysis', {}).get('topics', [])
            if topics:
                top_topic = topics[0] if topics else {}
                keywords = top_topic.get('keywords', [])[:10]
                weights = list(range(len(keywords), 0, -1))  # Простые веса
                
                fig.add_trace(
                    go.Bar(x=weights, y=keywords, orientation='h', name='Частота'),
                    row=3, col=1
                )
            
            # 6. Сетевые метрики
            network_metrics = analysis_results.get('network_analysis', {}).get('metrics', {})
            if network_metrics:
                metrics_names = ['Центральность', 'PageRank', 'Кластеризация', 'Связность']
                metrics_values = [
                    network_metrics.get('degree_centrality', 0),
                    network_metrics.get('pagerank', 0) * 100,  # Увеличиваем для отображения
                    network_metrics.get('clustering_coefficient', 0),
                    network_metrics.get('total_connections', 0) / 100  # Нормализуем
                ]
                
                fig.add_trace(
                    go.Bar(x=metrics_names, y=metrics_values, name='Значение'),
                    row=3, col=2
                )
            
            fig.update_layout(
                title_text=f"Анализ канала: {channel_data.get('name', 'Unknown')}",
                height=1200,
                showlegend=False
            )
            
            return fig.to_dict()
            
        except Exception as e:
            self.logger.error(f"Error creating channel analysis dashboard: {e}")
            return {}

class AlertingSystem:
    """Система оповещений и мониторинга"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.redis = None
        self.running = False
    
    async def initialize(self):
        """Инициализация системы мониторинга"""
        try:
            self.redis = aioredis.from_url(self.config.redis_url)
            await self.redis.ping()
            self.logger.info("Redis connection established")
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def start_monitoring(self):
        """Запуск мониторинга"""
        self.running = True
        self.logger.info("Starting monitoring system")
        
        while self.running:
            try:
                await self._run_monitoring_checks()
                await asyncio.sleep(self.config.check_interval_minutes * 60)
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)  # Ждем минуту перед повтором
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.running = False
        self.logger.info("Monitoring system stopped")
    
    async def _run_monitoring_checks(self):
        """Выполнение проверок мониторинга"""
        alerts = []
        
        # Проверка подозрительных связей
        suspicious_connections = await self._check_suspicious_connections()
        if suspicious_connections:
            alerts.extend(suspicious_connections)
        
        # Проверка аномалий в активности
        activity_anomalies = await self._check_activity_anomalies()
        if activity_anomalies:
            alerts.extend(activity_anomalies)
        
        # Проверка дубликатов контента
        duplicate_alerts = await self._check_duplicate_content()
        if duplicate_alerts:
            alerts.extend(duplicate_alerts)
        
        # Проверка роста каналов
        growth_alerts = await self._check_rapid_growth()
        if growth_alerts:
            alerts.extend(growth_alerts)
        
        # Отправка алертов
        if alerts:
            await self._send_alerts(alerts)
    
    async def _check_suspicious_connections(self) -> List[Dict]:
        """Проверка подозрительных связей между каналами"""
        alerts = []
        
        try:
            # Получаем данные о связях из Redis
            connections_data = await self.redis.get("recent_connections")
            if not connections_data:
                return alerts
            
            connections = json.loads(connections_data)
            
            for conn in connections:
                strength = conn.get('strength', 0.0)
                sync_posts = conn.get('synchronized_posts', 0)
                
                # Проверяем высокую схожесть
                if strength > self.config.thresholds['high_similarity_threshold']:
                    alerts.append({
                        'type': 'high_similarity',
                        'severity': 'high',
                        'message': f"Обнаружена высокая схожесть ({strength:.2f}) между каналами {conn.get('source_id')} и {conn.get('target_id')}",
                        'data': conn
                    })
                
                # Проверяем синхронные публикации
                if sync_posts > self.config.thresholds['suspicious_sync_threshold']:
                    alerts.append({
                        'type': 'suspicious_sync',
                        'severity': 'medium',
                        'message': f"Обнаружено {sync_posts} синхронных публикаций между каналами {conn.get('source_id')} и {conn.get('target_id')}",
                        'data': conn
                    })
            
        except Exception as e:
            self.logger.error(f"Error checking suspicious connections: {e}")
        
        return alerts
    
    async def _check_activity_anomalies(self) -> List[Dict]:
        """Проверка аномалий в активности каналов"""
        alerts = []
        
        try:
            # Получаем данные об активности
            activity_data = await self.redis.get("channel_activity")
            if not activity_data:
                return alerts
            
            activity = json.loads(activity_data)
            
            for channel_id, data in activity.items():
                current_activity = data.get('current_hour_posts', 0)
                avg_activity = data.get('average_hour_posts', 0)
                
                # Проверяем резкое увеличение активности
                if avg_activity > 0 and current_activity > avg_activity * 5:
                    alerts.append({
                        'type': 'activity_spike',
                        'severity': 'medium',
                        'message': f"Резкое увеличение активности канала {channel_id}: {current_activity} постов (норма: {avg_activity:.1f})",
                        'data': {'channel_id': channel_id, 'current': current_activity, 'average': avg_activity}
                    })
            
        except Exception as e:
            self.logger.error(f"Error checking activity anomalies: {e}")
        
        return alerts
    
    async def _check_duplicate_content(self) -> List[Dict]:
        """Проверка высокого уровня дубликатов"""
        alerts = []
        
        try:
            # Получаем данные о дубликатах
            duplicates_data = await self.redis.get("duplicate_analysis")
            if not duplicates_data:
                return alerts
            
            duplicates = json.loads(duplicates_data)
            
            for channel_id, data in duplicates.items():
                duplicate_rate = data.get('duplicate_rate', 0.0)
                
                if duplicate_rate > self.config.thresholds['duplicate_rate_threshold']:
                    alerts.append({
                        'type': 'high_duplicates',
                        'severity': 'medium',
                        'message': f"Высокий уровень дубликатов в канале {channel_id}: {duplicate_rate:.1%}",
                        'data': {'channel_id': channel_id, 'duplicate_rate': duplicate_rate}
                    })
            
        except Exception as e:
            self.logger.error(f"Error checking duplicate content: {e}")
        
        return alerts
    
    async def _check_rapid_growth(self) -> List[Dict]:
        """Проверка резкого роста каналов"""
        alerts = []
        
        try:
            # Получаем данные о росте
            growth_data = await self.redis.get("channel_growth")
            if not growth_data:
                return alerts
            
            growth = json.loads(growth_data)
            
            for channel_id, data in growth.items():
                growth_rate = data.get('daily_growth_rate', 0.0)
                
                if growth_rate > self.config.thresholds['rapid_growth_threshold']:
                    alerts.append({
                        'type': 'rapid_growth',
                        'severity': 'low',
                        'message': f"Быстрый рост канала {channel_id}: {growth_rate:.1%} за день",
                        'data': {'channel_id': channel_id, 'growth_rate': growth_rate}
                    })
            
        except Exception as e:
            self.logger.error(f"Error checking rapid growth: {e}")
        
        return alerts
    
    async def _send_alerts(self, alerts: List[Dict]):
        """Отправка алертов"""
        try:
            # Группируем алерты по важности
            high_priority = [a for a in alerts if a['severity'] == 'high']
            medium_priority = [a for a in alerts if a['severity'] == 'medium']
            low_priority = [a for a in alerts if a['severity'] == 'low']
            
            # Формируем сообщение
            message = self._format_alert_message(high_priority, medium_priority, low_priority)
            
            # Отправляем email
            if self.config.smtp_username and self.config.smtp_password:
                await self._send_email_alert(message, len(high_priority) > 0)
            
            # Сохраняем в Redis для истории
            alert_history = {
                'timestamp': datetime.now().isoformat(),
                'alerts': alerts,
                'total_count': len(alerts),
                'high_priority_count': len(high_priority)
            }
            
            await self.redis.lpush("alert_history", json.dumps(alert_history))
            await self.redis.ltrim("alert_history", 0, 999)  # Храним последние 1000 алертов
            
            self.logger.info(f"Sent {len(alerts)} alerts ({len(high_priority)} high priority)")
            
        except Exception as e:
            self.logger.error(f"Error sending alerts: {e}")
    
    def _format_alert_message(self, high: List[Dict], medium: List[Dict], low: List[Dict]) -> str:
        """Форматирование сообщения с алертами"""
        message = f"Отчет мониторинга системы анализа Telegram каналов\n"
        message += f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if high:
            message += "🔴 КРИТИЧЕСКИЕ АЛЕРТЫ:\n"
            for alert in high:
                message += f"- {alert['message']}\n"
            message += "\n"
        
        if medium:
            message += "🟡 ПРЕДУПРЕЖДЕНИЯ:\n"
            for alert in medium:
                message += f"- {alert['message']}\n"
            message += "\n"
        
        if low:
            message += "🔵 ИНФОРМАЦИОННЫЕ:\n"
            for alert in low:
                message += f"- {alert['message']}\n"
            message += "\n"
        
        message += f"Всего алертов: {len(high) + len(medium) + len(low)}\n"
        
        return message
    
    async def _send_email_alert(self, message: str, is_critical: bool = False):
        """Отправка email с алертом"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.smtp_username
            msg['To'] = self.config.alert_email
            
            subject = "🚨 Критический алерт" if is_critical else "📊 Отчет мониторинга"
            subject += f" - Система анализа Telegram каналов"
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            # Отправляем асинхронно
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_smtp_email, msg)
            
        except Exception as e:
            self.logger.error(f"Error sending email alert: {e}")
    
    def _send_smtp_email(self, msg):
        """Синхронная отправка email через SMTP"""
        with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
            server.starttls()
            server.login(self.config.smtp_username, self.config.smtp_password)
            server.send_message(msg)

class MetricsCollector:
    """Сборщик метрик для мониторинга"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis = None
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Инициализация подключения"""
        self.redis = aioredis.from_url(self.redis_url)
    
    async def update_channel_metrics(self, channel_id: int, metrics: Dict):
        """Обновление метрик канала"""
        try:
            # Сохраняем метрики с timestamp
            timestamped_metrics = {
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics
            }
            
            # Ключи для хранения
            current_key = f"channel_metrics:{channel_id}"
            history_key = f"channel_metrics_history:{channel_id}"
            
            # Сохраняем текущие метрики
            await self.redis.set(current_key, json.dumps(timestamped_metrics))
            
            # Добавляем в историю
            await self.redis.lpush(history_key, json.dumps(timestamped_metrics))
            await self.redis.ltrim(history_key, 0, 99)  # Храним последние 100 записей
            
            # Устанавливаем TTL
            await self.redis.expire(current_key, 86400 * 7)  # 7 дней
            await self.redis.expire(history_key, 86400 * 30)  # 30 дней
            
        except Exception as e:
            self.logger.error(f"Error updating channel metrics: {e}")
    
    async def get_system_overview(self) -> Dict:
        """Получение обзора системы"""
        try:
            # Получаем ключи всех каналов
            channel_keys = await self.redis.keys("channel_metrics:*")
            
            total_channels = len(channel_keys)
            active_channels = 0
            total_connections = 0
            total_posts = 0
            
            # Анализируем метрики каналов
            for key in channel_keys:
                data = await self.redis.get(key)
                if data:
                    metrics = json.loads(data)
                    channel_metrics = metrics.get('metrics', {})
                    
                    # Проверяем активность (посты за последний день)
                    last_activity = channel_metrics.get('last_post_time')
                    if last_activity:
                        last_time = datetime.fromisoformat(last_activity)
                        if (datetime.now() - last_time).days < 1:
                            active_channels += 1
                    
                    total_connections += channel_metrics.get('total_connections', 0)
                    total_posts += channel_metrics.get('posts_count', 0)
            
            return {
                'total_channels': total_channels,
                'active_channels': active_channels,
                'total_connections': total_connections,
                'total_posts': total_posts,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system overview: {e}")
            return {}

# Пример использования
async def main():
    # Конфигурация мониторинга
    config = MonitoringConfig(
        alert_email="admin@example.com",
        smtp_username="your_email@gmail.com",
        smtp_password="your_password"
    )
    
    # Инициализация компонентов
    visualizer = NetworkVisualizer()
    dashboard_generator = DashboardGenerator()
    alerting_system = AlertingSystem(config)
    metrics_collector = MetricsCollector(config.redis_url)
    
    try:
        # Инициализация
        await alerting_system.initialize()
        await metrics_collector.initialize()
        
        # Пример создания визуализаций
        channels = [
            {'id': 1, 'name': 'Channel 1', 'subscribers_count': 10000, 'theme': 'Tech', 'verified': True},
            {'id': 2, 'name': 'Channel 2', 'subscribers_count': 5000, 'theme': 'News', 'verified': False}
        ]
        
        connections = [
            {'source_id': 1, 'target_id': 2, 'strength': 0.8, 'connection_type': 'content_similarity'}
        ]
        
        # Создание сетевого графа
        network_graph = visualizer.create_network_graph(channels, connections, focus_channel_id=1)
        print(f"Network graph created with {len(network_graph['data'])} traces")
        
        # Запуск мониторинга (в реальном приложении это будет в отдельной задаче)
        # await alerting_system.start_monitoring()
        
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        alerting_system.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
