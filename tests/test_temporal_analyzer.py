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
