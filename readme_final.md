# 🔍 Система анализа взаимосвязанных каналов Telegram

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![React](https://img.shields.io/badge/React-18+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-20+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Комплексная система для автоматического выявления и анализа взаимосвязей между каналами Telegram на основе различных метрик и паттернов взаимодействия.

## 📋 Содержание

- [Особенности](#особенности)
- [Архитектура](#архитектура)
- [Быстрый старт](#быстрый-старт)
- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [Использование](#использование)
- [API документация](#api-документация)
- [Мониторинг](#мониторинг)
- [Разработка](#разработка)
- [FAQ](#faq)
- [Поддержка](#поддержка)

## ✨ Особенности

### 🔬 Многоуровневый анализ связей
- **Анализ контента**: Обнаружение дубликатов, семантическая схожесть, общие темы
- **Временной анализ**: Синхронные публикации, корреляция активности, паттерны публикаций
- **Сетевой анализ**: Общие администраторы, взаимные упоминания, структура связей
- **Тематический анализ**: Классификация по темам, ключевые слова, семантические кластеры

### 📊 Визуализация и аналитика
- Интерактивные графы сетей каналов
- Тепловые карты активности
- Временные линии событий
- Дашборды с ключевыми метриками
- Экспорт данных в различных форматах

### 🔍 Интеллектуальный поиск
- Многокритериальная фильтрация каналов
- Поиск по контенту и метаданным
- Сохранение и воспроизведение запросов
- Рекомендации похожих каналов

### 🚨 Мониторинг и алерты
- Обнаружение подозрительной активности
- Уведомления о новых связях
- Мониторинг ключевых слов
- Автоматические отчеты

### 🔒 Безопасность и соответствие
- Обработка только публичных данных
- Соблюдение Terms of Service Telegram
- Анонимизация персональных данных
- GDPR compliance

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Auth Service  │
│   (React)       │◄──►│   (Nginx)       │◄──►│   (JWT)         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Backend API   │    │   Data Collector│    │   Analysis      │
│   (FastAPI)     │◄──►│   (Telethon)    │◄──►│   Engine        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Database      │    │   Cache         │    │   Monitoring    │
│   (PostgreSQL)  │    │   (Redis)       │    │   (Grafana)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Компоненты системы

- **Frontend**: React-приложение с интерактивными визуализациями
- **Backend API**: FastAPI сервер с REST и WebSocket endpoints
- **Data Collector**: Сервис сбора данных из Telegram API
- **Analysis Engine**: Модуль анализа с ML алгоритмами
- **Database**: PostgreSQL с оптимизированными индексами
- **Cache**: Redis для кеширования и очередей задач
- **Monitoring**: Grafana + Prometheus для мониторинга

## 🚀 Быстрый старт

### Предварительные требования

- Docker 20.0+ и Docker Compose
- Git
- Минимум 4GB RAM
- 10GB свободного места на диске

### 1. Получение Telegram API ключей

1. Перейдите на [my.telegram.org](https://my.telegram.org)
2. Войдите в свой аккаунт Telegram
3. Перейдите в "API development tools"
4. Создайте новое приложение
5. Сохраните `api_id` и `api_hash`

### 2. Установка системы

```bash
# Клонирование репозитория
git clone https://github.com/your-repo/telegram-analysis.git
cd telegram-analysis

# Запуск автоматической установки
chmod +x install.sh
./install.sh
```

### 3. Конфигурация

```bash
# Редактирование конфигурации
nano .env

# Укажите ваши Telegram API ключи
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

### 4. Запуск системы

```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps
```

### 5. Доступ к интерфейсам

- 🌐 **Web интерфейс**: http://localhost:3000
- 🔌 **API**: http://localhost:8000
- 📊 **Grafana**: http://localhost:3001 (admin/admin)
- 📈 **Prometheus**: http://localhost:9090

## 📦 Установка

### Автоматическая установка (рекомендуется)

```bash
curl -sSL https://raw.githubusercontent.com/your-repo/telegram-analysis/main/install.sh | bash
```

### Ручная установка

<details>
<summary>Развернуть инструкции по ручной установке</summary>

#### 1. Системные зависимости

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y docker.io docker-compose git python3 python3-pip postgresql-client redis-tools
```

**CentOS/RHEL:**
```bash
sudo yum update
sudo yum install -y docker docker-compose git python3 python3-pip postgresql redis
sudo systemctl start docker
sudo systemctl enable docker
```

**macOS:**
```bash
brew install docker docker-compose git python3 postgresql redis
```

#### 2. Клонирование проекта

```bash
git clone https://github.com/your-repo/telegram-analysis.git
cd telegram-analysis
```

#### 3. Конфигурация окружения

```bash
cp .env.example .env
nano .env  # Отредактируйте конфигурацию
```

#### 4. Построение образов

```bash
docker-compose build
```

#### 5. Инициализация базы данных

```bash
docker-compose up -d postgres redis
sleep 10
docker-compose exec postgres psql -U telegram_user -d telegram_analysis -f /docker-entrypoint-initdb.d/init.sql
```

#### 6. Запуск сервисов

```bash
docker-compose up -d
```

</details>

## ⚙️ Конфигурация

### Основные параметры (.env)

```bash
# Telegram API (обязательно)
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# База данных
DATABASE_URL=postgresql://telegram_user:password@postgres:5432/telegram_analysis

# Redis
REDIS_URL=redis://redis:6379

# Безопасность
JWT_SECRET=your_secure_jwt_secret

# Email уведомления
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ALERT_EMAIL=admin@yourcompany.com

# Мониторинг
GRAFANA_PASSWORD=secure_password
```

### Расширенная конфигурация

<details>
<summary>Параметры анализа</summary>

```bash
# Пороги анализа
CONTENT_SIMILARITY_THRESHOLD=0.7
TIME_CORRELATION_THRESHOLD=0.6
DUPLICATE_THRESHOLD=0.85
NETWORK_ANALYSIS_DEPTH=3

# Производительность
ANALYSIS_WORKERS=4
COLLECTOR_BATCH_SIZE=100
COLLECTOR_RATE_LIMIT=1

# Алгоритмы
SEMANTIC_MODEL=all-MiniLM-L6-v2
CLUSTERING_EPS=0.3
CLUSTERING_MIN_SAMPLES=3
```

</details>

<details>
<summary>Мониторинг и алерты</summary>

```bash
# Пороги алертов
HIGH_SIMILARITY_THRESHOLD=0.85
SUSPICIOUS_SYNC_THRESHOLD=10
RAPID_GROWTH_THRESHOLD=0.2
DUPLICATE_RATE_THRESHOLD=0.3

# Интервалы проверок
CHECK_INTERVAL_MINUTES=30
BACKUP_INTERVAL_HOURS=24
CLEANUP_INTERVAL_DAYS=7
```

</details>

## 🎯 Использование

### Web интерфейс

1. **Поиск каналов**
   - Откройте http://localhost:3000
   - Используйте фильтры для поиска каналов
   - Просматривайте метрики и статистику

2. **Анализ связей**
   - Выберите канал для анализа
   - Запустите комплексный анализ
   - Изучите результаты в интерактивных графах

3. **Мониторинг**
   - Настройте алерты на подозрительную активность
   - Отслеживайте изменения в сети каналов
   - Экспортируйте отчеты

### API использование

```python
import httpx

# Создание клиента
client = httpx.Client(base_url="http://localhost:8000")

# Получение списка каналов
channels = client.get("/channels", params={
    "theme": "Технологии",
    "min_subscribers": 1000
}).json()

# Запуск анализа канала
analysis = client.post(f"/channels/{channel_id}/analyze", json={
    "analysis_types": ["content", "temporal", "network"],
    "depth": 2
}).json()

# Получение результатов
results = client.get(f"/analysis/{channel_id}").json()
```

### CLI команды

```bash
# Управление сервисами
make up          # Запуск всех сервисов
make down        # Остановка сервисов
make restart     # Перезапуск
make logs        # Просмотр логов
make status      # Статус сервисов

# Управление данными
make backup      # Создание бэкапа
make restore     # Восстановление из бэкапа
make migrate     # Выполнение миграций
make clean       # Очистка системы

# Мониторинг
make monitor     # Проверка здоровья системы
make stats       # Статистика использования ресурсов
make test        # Запуск тестов

# Обновление
make update      # Обновление системы
```

## 📚 API документация

### Основные эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/channels` | Список каналов с фильтрацией |
| GET | `/channels/{id}` | Информация о канале |
| POST | `/channels/{id}/analyze` | Запуск анализа |
| GET | `/analysis/{id}` | Результаты анализа |
| GET | `/connections` | Связи между каналами |
| GET | `/stats/overview` | Общая статистика |

### Интерактивная документация

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Примеры запросов

<details>
<summary>Поиск каналов</summary>

```bash
curl -X GET "http://localhost:8000/channels?search=tech&min_subscribers=1000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

</details>

<details>
<summary>Анализ канала</summary>

```bash
curl -X POST "http://localhost:8000/channels/1/analyze" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "analysis_types": ["content", "temporal", "network"],
    "depth": 2
  }'
```

</details>

## 📊 Мониторинг

### Grafana дашборды

1. **Обзор системы**
   - Количество каналов и связей
   - Активность анализа
   - Использование ресурсов

2. **Качество данных**
   - Скорость сбора данных
   - Ошибки API
   - Статистика дубликатов

3. **Производительность**
   - Время отклика API
   - Нагрузка на базу данных
   - Использование памяти

### Алерты

Система автоматически отправляет уведомления о:
- Подозрительно высокой схожести между каналами
- Массовых синхронных публикациях
- Резких изменениях в активности
- Технических проблемах

### Логи

```bash
# Просмотр логов всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f api
docker-compose logs -f collector
docker-compose logs -f analyzer

# Поиск ошибок
docker-compose logs | grep ERROR
```

## 🛠️ Разработка

### Настройка окружения разработки

```bash
# Клонирование репозитория
git clone https://github.com/your-repo/telegram-analysis.git
cd telegram-analysis

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.dev.txt

# Запуск в режиме разработки
docker-compose -f docker-compose.dev.yml up -d
```

### Структура проекта

```
telegram-analysis/
├── api/                    # Backend API
│   ├── main.py            # Основной файл FastAPI
│   ├── database.py        # Модели базы данных
│   └── routers/           # API роутеры
├── collector/             # Сборщик данных
│   ├── telegram_collector.py
│   └── config.py
├── analyzer/              # Движок анализа
│   ├── analysis_engine.py
│   └── algorithms/
├── monitor/               # Мониторинг
│   └── visualization_monitoring.py
├── frontend/              # React приложение
│   ├── src/
│   └── public/
├── tests/                 # Тесты
├── docs/                  # Документация
├── scripts/               # Скрипты управления
└── docker-compose.yml     # Docker конфигурация
```

### Тестирование

```bash
# Запуск всех тестов
pytest

# Тесты с покрытием
pytest --cov=. --cov-report=html

# Тесты конкретного модуля
pytest tests/test_api.py

# Интеграционные тесты
pytest tests/integration/
```

### Добавление новых функций

1. **Создание ветки**
```bash
git checkout -b feature/new-analysis-algorithm
```

2. **Разработка**
```bash
# Добавление нового алгоритма в analyzer/algorithms/
# Создание тестов в tests/
# Обновление документации
```

3. **Тестирование**
```bash
pytest tests/
docker-compose -f docker-compose.test.yml up
```

4. **Pull Request**
```bash
git push origin feature/new-analysis-algorithm
# Создание PR в GitHub
```

### Coding Standards

- **Python**: PEP 8, type hints, docstrings
- **JavaScript**: ESLint, Prettier
- **Commit messages**: Conventional Commits
- **Testing**: Минимум 80% покрытия кода

## ❓ FAQ

<details>
<summary><strong>Q: Как получить Telegram API ключи?</strong></summary>

A: Перейдите на https://my.telegram.org, войдите в аккаунт, создайте приложение в разделе "API development tools".
</details>

<details>
<summary><strong>Q: Система не видит новые каналы</strong></summary>

A: Убедитесь, что:
1. Каналы публичные
2. API ключи корректные
3. Сервис collector запущен
4. Нет ограничений Telegram API
</details>

<details>
<summary><strong>Q: Высокое потребление памяти</strong></summary>

A: 
1. Уменьшите `ANALYSIS_WORKERS` в .env
2. Настройте `COLLECTOR_BATCH_SIZE`
3. Увеличьте интервалы анализа
4. Настройте автоочистку старых данных
</details>

<details>
<summary><strong>Q: Ошибки подключения к базе данных</strong></summary>

A:
1. Проверьте `DATABASE_URL` в .env
2. Убедитесь, что PostgreSQL запущен
3. Проверьте пароли и права доступа
4. Выполните миграции: `make migrate`
</details>

<details>
<summary><strong>Q: Как добавить новый тип анализа?</strong></summary>

A:
1. Создайте класс анализатора в `analyzer/algorithms/`
2. Добавьте в `MainAnalysisEngine`
3. Обновите API endpoints
4. Добавьте тесты
5. Обновите документацию
</details>

## 🔧 Устранение неполадок

### Проблемы с установкой

```bash
# Проверка Docker
docker --version
docker-compose --version

# Проверка портов
netstat -tlnp | grep -E '(3000|8000|5432|6379)'

# Очистка Docker
docker system prune -af
docker volume prune -f
```

### Проблемы с производительностью

```bash
# Мониторинг ресурсов
docker stats

# Проверка логов
docker-compose logs --tail=100 api | grep ERROR

# Оптимизация базы данных
docker-compose exec postgres psql -U telegram_user -d telegram_analysis -c "VACUUM ANALYZE;"
```

### Проблемы с Telegram API

```bash
# Проверка подключения
docker-compose exec collector python -c "
from telethon import TelegramClient
client = TelegramClient('test', API_ID, API_HASH)
client.start()
print('Connected successfully')
"

# Проверка лимитов
grep -i "flood" logs/collector.log
```

## 🤝 Содействие проекту

Мы приветствуем ваш вклад в развитие проекта!

### Как помочь

1. **Сообщения об ошибках**: Создавайте issues с подробным описанием
2. **Предложения функций**: Обсуждайте идеи в Discussions
3. **Код**: Создавайте Pull Requests
4. **Документация**: Улучшайте и дополняйте документацию
5. **Тестирование**: Помогайте тестировать новые функции

### Процесс разработки

1. Fork проекта
2. Создайте feature branch
3. Внесите изменения
4. Добавьте тесты
5. Убедитесь, что все тесты проходят
6. Создайте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. Подробности в файле [LICENSE](LICENSE).

## 👥 Авторы

- **Главный разработчик**: [@developer](https://github.com/developer)
- **Архитектор**: [@architect](https://github.com/architect)
- **Участники**: См. [CONTRIBUTORS.md](CONTRIBUTORS.md)

## 🆘 Поддержка

### Получение помощи

- 📧 **Email**: support@telegram-analysis.com
- 💬 **Telegram**: @telegram_analysis_support
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/telegram-analysis/issues)
- 💡 **Discussions**: [GitHub Discussions](https://github.com/your-repo/telegram-analysis/discussions)

### Коммерческая поддержка

Для коммерческого использования и расширенной поддержки:
- 🏢 **Enterprise**: enterprise@telegram-analysis.com
- 📞 **Консультации**: +7 (XXX) XXX-XX-XX

## 🔗 Полезные ссылки

- [📖 Документация](https://docs.telegram-analysis.com)
- [🎥 Видеоуроки](https://youtube.com/telegram-analysis)
- [📊 Примеры использования](https://examples.telegram-analysis.com)
- [🔧 API Reference](https://api.telegram-analysis.com)
- [🚀 Roadmap](https://github.com/your-repo/telegram-analysis/projects)

---

<div align="center">

**⭐ Если проект оказался полезным, поставьте звезду на GitHub!**

Made with ❤️ by [Telegram Analysis Team](https://github.com/your-repo)

</div>
