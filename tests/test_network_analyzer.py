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
