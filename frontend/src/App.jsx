import React, { useState, useEffect, useMemo } from 'react';
import { Search, Users, MessageCircle, Link, BarChart3, Network, Calendar, Filter, Download, Eye, Plus } from 'lucide-react';

// Симулированные данные
const generateChannels = () => {
  const themes = ['Политика', 'Технологии', 'Новости', 'Спорт', 'Бизнес', 'Развлечения'];
  const channels = [];
  
  for (let i = 1; i <= 50; i++) {
    channels.push({
      id: i,
      name: `Канал ${i}`,
      username: `@channel${i}`,
      description: `Описание канала ${i} - качественный контент по теме`,
      subscribers: Math.floor(Math.random() * 100000) + 1000,
      theme: themes[Math.floor(Math.random() * themes.length)],
      posts: Math.floor(Math.random() * 1000) + 100,
      avgViews: Math.floor(Math.random() * 50000) + 500,
      createdAt: new Date(2020 + Math.random() * 4, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28)),
      lastPost: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000),
      verified: Math.random() > 0.7,
      connections: []
    });
  }
  
  // Добавляем связи между каналами
  channels.forEach(channel => {
    const numConnections = Math.floor(Math.random() * 8) + 1;
    const connectionTypes = ['content_similarity', 'time_correlation', 'admin_overlap', 'cross_posting'];
    
    for (let j = 0; j < numConnections; j++) {
      const targetId = Math.floor(Math.random() * 50) + 1;
      if (targetId !== channel.id) {
        channel.connections.push({
          targetId,
          type: connectionTypes[Math.floor(Math.random() * connectionTypes.length)],
          strength: Math.random(),
          lastUpdated: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000)
        });
      }
    }
  });
  
  return channels;
};

const connectionTypeLabels = {
  content_similarity: 'Схожий контент',
  time_correlation: 'Временная корреляция', 
  admin_overlap: 'Общие админы',
  cross_posting: 'Кросс-постинг'
};

const TelegramAnalysisApp = () => {
  const [channels] = useState(generateChannels());
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTheme, setSelectedTheme] = useState('');
  const [selectedChannel, setSelectedChannel] = useState(null);
  const [minSubscribers, setMinSubscribers] = useState(0);
  const [activeTab, setActiveTab] = useState('search');
  const [analysisResults, setAnalysisResults] = useState(null);

  const themes = [...new Set(channels.map(c => c.theme))];

  const filteredChannels = useMemo(() => {
    return channels.filter(channel => {
      const matchesSearch = channel.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          channel.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          channel.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesTheme = !selectedTheme || channel.theme === selectedTheme;
      const matchesSubscribers = channel.subscribers >= minSubscribers;
      
      return matchesSearch && matchesTheme && matchesSubscribers;
    });
  }, [channels, searchTerm, selectedTheme, minSubscribers]);

  const analyzeChannel = (channel) => {
    setSelectedChannel(channel);
    
    // Получаем связанные каналы
    const connectedChannels = channel.connections.map(conn => {
      const target = channels.find(c => c.id === conn.targetId);
      return target ? { ...target, connection: conn } : null;
    }).filter(Boolean);

    // Группируем по типам связей
    const connectionsByType = connectedChannels.reduce((acc, ch) => {
      const type = ch.connection.type;
      if (!acc[type]) acc[type] = [];
      acc[type].push(ch);
      return acc;
    }, {});

    // Анализ контента
    const contentAnalysis = {
      duplicateContent: Math.floor(Math.random() * 30) + 5,
      similarThemes: connectedChannels.filter(ch => ch.theme === channel.theme).length,
      averageSimilarity: (connectedChannels.reduce((sum, ch) => sum + ch.connection.strength, 0) / connectedChannels.length).toFixed(2)
    };

    // Временной анализ
    const timeAnalysis = {
      correlatedPublishing: connectedChannels.filter(ch => ch.connection.type === 'time_correlation').length,
      averageDelay: Math.floor(Math.random() * 120) + 5, // минуты
      peakActivity: `${Math.floor(Math.random() * 12) + 8}:00-${Math.floor(Math.random() * 12) + 20}:00`
    };

    setAnalysisResults({
      channel,
      connectedChannels,
      connectionsByType,
      contentAnalysis,
      timeAnalysis,
      networkMetrics: {
        centrality: Math.random().toFixed(3),
        clustering: Math.random().toFixed(3),
        pagerank: Math.random().toFixed(4)
      }
    });
    setActiveTab('analysis');
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  const formatDate = (date) => {
    return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const NetworkGraph = ({ connections }) => {
    const nodes = [];
    const links = [];
    
    // Центральный узел
    nodes.push({ id: 'center', name: selectedChannel.name, type: 'main', x: 200, y: 200 });
    
    // Связанные узлы
    connections.forEach((ch, idx) => {
      const angle = (idx / connections.length) * 2 * Math.PI;
      const radius = 120;
      const x = 200 + Math.cos(angle) * radius;
      const y = 200 + Math.sin(angle) * radius;
      
      nodes.push({ 
        id: ch.id, 
        name: ch.name, 
        type: ch.connection.type, 
        strength: ch.connection.strength,
        x, y 
      });
      
      links.push({ 
        source: 'center', 
        target: ch.id, 
        strength: ch.connection.strength,
        type: ch.connection.type
      });
    });

    const getNodeColor = (type) => {
      const colors = {
        main: '#3b82f6',
        content_similarity: '#10b981',
        time_correlation: '#f59e0b',
        admin_overlap: '#ef4444',
        cross_posting: '#8b5cf6'
      };
      return colors[type] || '#6b7280';
    };

    const getStrokeWidth = (strength) => Math.max(1, strength * 5);

    return (
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Network className="h-5 w-5" />
          Граф связей
        </h3>
        <svg width="400" height="400" className="border rounded">
          {/* Связи */}
          {links.map((link, idx) => {
            const sourceNode = nodes.find(n => n.id === link.source);
            const targetNode = nodes.find(n => n.id === link.target);
            return (
              <line
                key={idx}
                x1={sourceNode.x}
                y1={sourceNode.y}
                x2={targetNode.x}
                y2={targetNode.y}
                stroke={getNodeColor(link.type)}
                strokeWidth={getStrokeWidth(link.strength)}
                opacity={0.6}
              />
            );
          })}
          
          {/* Узлы */}
          {nodes.map(node => (
            <g key={node.id}>
              <circle
                cx={node.x}
                cy={node.y}
                r={node.type === 'main' ? 15 : 8}
                fill={getNodeColor(node.type)}
                stroke="#fff"
                strokeWidth="2"
              />
              <text
                x={node.x}
                y={node.y + 25}
                textAnchor="middle"
                fontSize="10"
                fill="#374151"
                className="font-medium"
              >
                {node.name.length > 15 ? node.name.slice(0, 15) + '...' : node.name}
              </text>
            </g>
          ))}
        </svg>
        
        {/* Легенда */}
        <div className="mt-4 space-y-2">
          <h4 className="font-medium text-sm">Типы связей:</h4>
          {Object.entries(connectionTypeLabels).map(([type, label]) => (
            <div key={type} className="flex items-center gap-2 text-sm">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: getNodeColor(type) }}
              ></div>
              <span>{label}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Заголовок */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <MessageCircle className="h-8 w-8 text-blue-600" />
            Анализ Telegram каналов
          </h1>
          <p className="text-gray-600 mt-1">Сервис для выявления взаимосвязей между каналами</p>
        </div>
      </div>

      {/* Навигация */}
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex gap-4 border-b">
          <button
            onClick={() => setActiveTab('search')}
            className={`pb-2 px-1 font-medium text-sm ${
              activeTab === 'search' 
                ? 'border-b-2 border-blue-600 text-blue-600' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Поиск каналов
          </button>
          <button
            onClick={() => setActiveTab('analysis')}
            className={`pb-2 px-1 font-medium text-sm ${
              activeTab === 'analysis' 
                ? 'border-b-2 border-blue-600 text-blue-600' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Анализ связей
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'search' && (
          <div className="space-y-6">
            {/* Фильтры */}
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Filter className="h-5 w-5" />
                Поиск и фильтры
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Поиск
                  </label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Название или @username"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Тематика
                  </label>
                  <select
                    value={selectedTheme}
                    onChange={(e) => setSelectedTheme(e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="">Все темы</option>
                    {themes.map(theme => (
                      <option key={theme} value={theme}>{theme}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Мин. подписчиков
                  </label>
                  <input
                    type="number"
                    value={minSubscribers}
                    onChange={(e) => setMinSubscribers(Number(e.target.value))}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="0"
                  />
                </div>
                
                <div className="flex items-end">
                  <button className="w-full bg-blue-600 text-white rounded-md px-4 py-2 text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    Применить
                  </button>
                </div>
              </div>
            </div>

            {/* Статистика */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-lg border p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Найдено каналов</p>
                    <p className="text-2xl font-bold text-gray-900">{filteredChannels.length}</p>
                  </div>
                  <MessageCircle className="h-8 w-8 text-blue-600" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg border p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Общие подписчики</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatNumber(filteredChannels.reduce((sum, ch) => sum + ch.subscribers, 0))}
                    </p>
                  </div>
                  <Users className="h-8 w-8 text-green-600" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg border p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Связей выявлено</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {filteredChannels.reduce((sum, ch) => sum + ch.connections.length, 0)}
                    </p>
                  </div>
                  <Link className="h-8 w-8 text-purple-600" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg border p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Активных тем</p>
                    <p className="text-2xl font-bold text-gray-900">{themes.length}</p>
                  </div>
                  <BarChart3 className="h-8 w-8 text-orange-600" />
                </div>
              </div>
            </div>

            {/* Результаты поиска */}
            <div className="bg-white rounded-lg border">
              <div className="p-6 border-b">
                <h2 className="text-lg font-semibold">Результаты поиска</h2>
              </div>
              
              <div className="divide-y">
                {filteredChannels.slice(0, 20).map(channel => (
                  <div key={channel.id} className="p-6 hover:bg-gray-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-semibold text-gray-900">{channel.name}</h3>
                          <span className="text-gray-500 text-sm">{channel.username}</span>
                          {channel.verified && (
                            <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                              Verified
                            </span>
                          )}
                          <span className="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded-full">
                            {channel.theme}
                          </span>
                        </div>
                        
                        <p className="text-gray-600 text-sm mb-3">{channel.description}</p>
                        
                        <div className="flex items-center gap-6 text-sm text-gray-500">
                          <div className="flex items-center gap-1">
                            <Users className="h-4 w-4" />
                            {formatNumber(channel.subscribers)} подписчиков
                          </div>
                          <div className="flex items-center gap-1">
                            <MessageCircle className="h-4 w-4" />
                            {channel.posts} постов
                          </div>
                          <div className="flex items-center gap-1">
                            <Eye className="h-4 w-4" />
                            {formatNumber(channel.avgViews)} просмотров
                          </div>
                          <div className="flex items-center gap-1">
                            <Calendar className="h-4 w-4" />
                            Создан {formatDate(channel.createdAt)}
                          </div>
                          <div className="flex items-center gap-1">
                            <Link className="h-4 w-4" />
                            {channel.connections.length} связей
                          </div>
                        </div>
                      </div>
                      
                      <button
                        onClick={() => analyzeChannel(channel)}
                        className="ml-4 bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        Анализировать
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analysis' && analysisResults && (
          <div className="space-y-6">
            {/* Заголовок анализа */}
            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">{analysisResults.channel.name}</h2>
                  <p className="text-gray-600 mb-4">{analysisResults.channel.description}</p>
                  
                  <div className="flex items-center gap-6 text-sm">
                    <div className="flex items-center gap-1">
                      <Users className="h-4 w-4 text-gray-500" />
                      {formatNumber(analysisResults.channel.subscribers)} подписчиков
                    </div>
                    <div className="flex items-center gap-1">
                      <MessageCircle className="h-4 w-4 text-gray-500" />
                      {analysisResults.channel.posts} постов
                    </div>
                    <div className="flex items-center gap-1">
                      <Link className="h-4 w-4 text-gray-500" />
                      {analysisResults.connectedChannels.length} связанных каналов
                    </div>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <button className="bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-700 flex items-center gap-2">
                    <Download className="h-4 w-4" />
                    Экспорт
                  </button>
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 flex items-center gap-2">
                    <Plus className="h-4 w-4" />
                    В коллекцию
                  </button>
                </div>
              </div>
            </div>

            {/* Метрики и граф */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Сетевые метрики */}
              <div className="bg-white rounded-lg border p-6">
                <h3 className="text-lg font-semibold mb-4">Сетевые метрики</h3>
                
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium text-gray-700">Центральность</span>
                      <span className="text-sm text-gray-900">{analysisResults.networkMetrics.centrality}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${analysisResults.networkMetrics.centrality * 100}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium text-gray-700">Кластеризация</span>
                      <span className="text-sm text-gray-900">{analysisResults.networkMetrics.clustering}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-600 h-2 rounded-full" 
                        style={{ width: `${analysisResults.networkMetrics.clustering * 100}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium text-gray-700">PageRank</span>
                      <span className="text-sm text-gray-900">{analysisResults.networkMetrics.pagerank}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-purple-600 h-2 rounded-full" 
                        style={{ width: `${analysisResults.networkMetrics.pagerank * 10000}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                <div className="mt-6 grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">{analysisResults.contentAnalysis.duplicateContent}%</div>
                    <div className="text-xs text-gray-600">Дубликаты контента</div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">{analysisResults.timeAnalysis.correlatedPublishing}</div>
                    <div className="text-xs text-gray-600">Временные корреляции</div>
                  </div>
                </div>
              </div>

              {/* Граф связей */}
              <NetworkGraph connections={analysisResults.connectedChannels} />
            </div>

            {/* Связанные каналы */}
            <div className="bg-white rounded-lg border">
              <div className="p-6 border-b">
                <h3 className="text-lg font-semibold">Связанные каналы ({analysisResults.connectedChannels.length})</h3>
              </div>
              
              <div className="divide-y max-h-96 overflow-y-auto">
                {analysisResults.connectedChannels.map(channel => (
                  <div key={channel.id} className="p-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium text-gray-900">{channel.name}</h4>
                          <span className="text-gray-500 text-sm">{channel.username}</span>
                          <span className="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded-full">
                            {connectionTypeLabels[channel.connection.type]}
                          </span>
                        </div>
                        
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span>{formatNumber(channel.subscribers)} подписчиков</span>
                          <span>Сила связи: {(channel.connection.strength * 100).toFixed(1)}%</span>
                          <span>Обновлено: {formatDate(channel.connection.lastUpdated)}</span>
                        </div>
                      </div>
                      
                      <button
                        onClick={() => analyzeChannel(channel)}
                        className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                      >
                        Анализировать
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Детальная аналитика */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg border p-6">
                <h3 className="text-lg font-semibold mb-4">Анализ контента</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Схожие темы:</span>
                    <span className="font-medium">{analysisResults.contentAnalysis.similarThemes} каналов</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Средняя схожесть:</span>
                    <span className="font-medium">{analysisResults.contentAnalysis.averageSimilarity}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Дубликаты контента:</span>
                    <span className="font-medium">{analysisResults.contentAnalysis.duplicateContent}%</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg border p-6">
                <h3 className="text-lg font-semibold mb-4">Временной анализ</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Коррелированные публикации:</span>
                    <span className="font-medium">{analysisResults.timeAnalysis.correlatedPublishing}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Средняя задержка:</span>
                    <span className="font-medium">{analysisResults.timeAnalysis.averageDelay} мин</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Пик активности:</span>
                    <span className="font-medium">{analysisResults.timeAnalysis.peakActivity}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analysis' && !analysisResults && (
          <div className="bg-white rounded-lg border p-12 text-center">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Выберите канал для анализа</h3>
            <p className="text-gray-600">Используйте поиск каналов, чтобы найти интересующий вас канал и провести анализ его связей</p>
            <button
              onClick={() => setActiveTab('search')}
              className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
            >
              Перейти к поиску
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default TelegramAnalysisApp;