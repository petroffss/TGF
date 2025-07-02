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
