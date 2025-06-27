#!/bin/bash
# auto-setup.sh - Автоматическое создание проекта Telegram Analysis

set -e

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

create_project_structure() {
    print_info "Создание структуры проекта..."
    
    PROJECT_NAME="telegram-analysis"
    mkdir -p $PROJECT_NAME
    cd $PROJECT_NAME
    
    # Создание директорий
    mkdir -p {frontend/src,scripts,tests,nginx/{ssl,logs},prometheus,redis,sql,docs,logs,backups,models}
    
    print_success "Структура директорий создана"
}

create_main_files() {
    print_info "Создание основных файлов..."
    
    # README.md
    cat > README.md << 'EOF'
# 🔍 Система анализа взаимосвязанных каналов Telegram

Комплексная система для автоматического выявления и анализа взаимосвязей между каналами Telegram.

## 🚀 Быстрый старт

1. Получите Telegram API ключи на https://my.telegram.org
2. Отредактируйте файл .env
3. Запустите: `./scripts/install.sh`
4. Откройте: http://localhost:3000

## 📖 Документация

- Web интерфейс: http://localhost:3000
- API документация: http://localhost:8000/docs
- Grafana мониторинг: http://localhost:3001

## 🛠️ Управление

```bash
make up          # Запуск
make down        # Остановка
make logs        # Логи
make backup      # Бэкап
make test        # Тесты
```
EOF

    # docker-compose.yml
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: telegram_analysis_db
    environment:
      POSTGRES_DB: telegram_analysis
      POSTGRES_USER: telegram_user
      POSTGRES_PASSWORD: secure_password_123
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - telegram_network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: telegram_analysis_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./redis/redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    networks:
      - telegram_network
    restart: unless-stopped

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: telegram_analysis_api
    environment:
      - DATABASE_URL=postgresql://telegram_user:secure_password_123@postgres:5432/telegram_analysis
      - REDIS_URL=redis://redis:6379
      - TELEGRAM_API_ID=${TELEGRAM_API_ID}
      - TELEGRAM_API_HASH=${TELEGRAM_API_HASH}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
    networks:
      - telegram_network
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: telegram_analysis_frontend
    ports:
      - "3000:80"
    depends_on:
      - api
    networks:
      - telegram_network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: telegram_analysis_grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - telegram_network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  grafana_data:

networks:
  telegram_network:
    driver: bridge
EOF

    # .env.example
    cat > .env.example << 'EOF'
# Telegram API (получите на https://my.telegram.org)
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here

# Database
DATABASE_URL=postgresql://telegram_user:secure_password_123@postgres:5432/telegram_analysis

# Redis
REDIS_URL=redis://redis:6379

# JWT Secret
JWT_SECRET=your_very_secure_jwt_secret_key_here

# Email настройки
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ALERT_EMAIL=admin@yourcompany.com

# Environment
ENVIRONMENT=production
EOF

    # Makefile
    cat > Makefile << 'EOF'
.PHONY: up down logs build test backup

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

build:
	docker-compose build

test:
	docker-compose exec api pytest

backup:
	./scripts/backup.sh

status:
	docker-compose ps

clean:
	docker-compose down -v
	docker system prune -af
EOF

    print_success "Основные файлы созданы"
}

create_backend_files() {
    print_info "Создание backend файлов..."
    
    # main.py
    cat > main.py << 'EOF'
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Telegram Channels Analysis API",
    description="API для анализа взаимосвязанных каналов Telegram",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Telegram Channels Analysis API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/channels")
async def get_channels():
    # Имитация данных каналов
    return [
        {
            "id": 1,
            "name": "Демо канал 1",
            "username": "@demo1",
            "description": "Демонстрационный канал",
            "subscribers": 10000,
            "theme": "Технологии"
        },
        {
            "id": 2,
            "name": "Демо канал 2", 
            "username": "@demo2",
            "description": "Еще один демо канал",
            "subscribers": 5000,
            "theme": "Новости"
        }
    ]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

    # requirements.txt
    cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
pydantic==2.5.0
python-jose[cryptography]==3.3.0
httpx==0.25.2
pytest==7.4.3
EOF

    # Dockerfile.api
    cat > Dockerfile.api << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc postgresql-client curl

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    print_success "Backend файлы созданы"
}

create_frontend_files() {
    print_info "Создание frontend файлов..."
    
    # frontend/Dockerfile
    cat > frontend/Dockerfile << 'EOF'
FROM nginx:alpine

COPY index.html /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
EOF

    # frontend/index.html
    cat > frontend/index.html << 'EOF'
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Анализ Telegram каналов</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #007bff; }
        .channels-list { margin-top: 30px; }
        .channel-item { background: white; border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Система анализа Telegram каналов</h1>
            <p>Комплексная платформа для выявления взаимосвязей между каналами</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="total-channels">0</div>
                <div>Всего каналов</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="total-connections">0</div>
                <div>Связей найдено</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="analysis-tasks">0</div>
                <div>Анализов выполнено</div>
            </div>
        </div>
        
        <div class="channels-list">
            <h2>Каналы в системе</h2>
            <div id="channels-container">
                <p>Загрузка каналов...</p>
            </div>
        </div>
    </div>

    <script>
        // Загрузка данных с API
        async function loadData() {
            try {
                const response = await fetch('/api/channels');
                const channels = await response.json();
                
                document.getElementById('total-channels').textContent = channels.length;
                document.getElementById('total-connections').textContent = Math.floor(Math.random() * 100);
                document.getElementById('analysis-tasks').textContent = Math.floor(Math.random() * 50);
                
                const container = document.getElementById('channels-container');
                container.innerHTML = channels.map(channel => `
                    <div class="channel-item">
                        <h3>${channel.name} (${channel.username})</h3>
                        <p>${channel.description}</p>
                        <p><strong>Подписчиков:</strong> ${channel.subscribers.toLocaleString()}</p>
                        <p><strong>Тема:</strong> ${channel.theme}</p>
                        <button class="btn" onclick="analyzeChannel(${channel.id})">
                            Анализировать
                        </button>
                    </div>
                `).join('');
                
            } catch (error) {
                console.error('Ошибка загрузки данных:', error);
                document.getElementById('channels-container').innerHTML = 
                    '<p>Ошибка загрузки данных. Убедитесь, что API сервер запущен.</p>';
            }
        }
        
        function analyzeChannel(id) {
            alert(`Запуск анализа канала ${id}...`);
        }
        
        // Загрузка данных при загрузке страницы
        loadData();
        
        // Обновление данных каждые 30 секунд
        setInterval(loadData, 30000);
    </script>
</body>
</html>
EOF

    # frontend/nginx.conf
    cat > frontend/nginx.conf << 'EOF'
events { worker_connections 1024; }

http {
    include /etc/nginx/mime.types;
    
    upstream api {
        server api:8000;
    }
    
    server {
        listen 80;
        
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files $uri $uri/ /index.html;
        }
        
        location /api/ {
            proxy_pass http://api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
EOF

    print_success "Frontend файлы созданы"
}

create_scripts() {
    print_info "Создание скриптов управления..."
    
    # scripts/install.sh
    cat > scripts/install.sh << 'EOF'
#!/bin/bash
echo "🚀 Установка системы анализа Telegram каналов..."

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и повторите попытку."
    exit 1
fi

# Создание .env файла из примера
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Создан .env файл. Отредактируйте его и укажите ваши Telegram API ключи."
fi

# Построение образов
echo "🔨 Построение Docker образов..."
docker-compose build

# Запуск сервисов
echo "🚀 Запуск сервисов..."
docker-compose up -d

# Ожидание запуска
echo "⏳ Ожидание запуска сервисов..."
sleep 30

# Проверка состояния
echo "✅ Проверка состояния сервисов..."
docker-compose ps

echo ""
echo "🎉 Установка завершена!"
echo ""
echo "📍 Доступные сервисы:"
echo "   🌐 Web интерфейс:  http://localhost:3000"
echo "   🔌 API:            http://localhost:8000"
echo "   📊 Grafana:        http://localhost:3001 (admin/admin123)"
echo ""
echo "⚠️  Не забудьте отредактировать .env файл!"
echo "   Укажите ваши TELEGRAM_API_ID и TELEGRAM_API_HASH"
echo ""
EOF

    # scripts/backup.sh
    cat > scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

echo "📦 Создание бэкапа базы данных..."
docker-compose exec -T postgres pg_dump -U telegram_user telegram_analysis | gzip > "$BACKUP_DIR/database_$DATE.sql.gz"

echo "📦 Создание бэкапа конфигурации..."
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" .env docker-compose.yml

echo "✅ Бэкап создан: $BACKUP_DIR/"
ls -la $BACKUP_DIR/
EOF

    # scripts/update.sh
    cat > scripts/update.sh << 'EOF'
#!/bin/bash
echo "🔄 Обновление системы..."

# Создание бэкапа
./scripts/backup.sh

# Обновление образов
docker-compose pull
docker-compose build --no-cache

# Перезапуск
docker-compose down
docker-compose up -d

echo "✅ Обновление завершено!"
EOF

    # Права доступа на скрипты
    chmod +x scripts/*.sh
    
    print_success "Скрипты созданы"
}

create_config_files() {
    print_info "Создание конфигурационных файлов..."
    
    # sql/init.sql
    cat > sql/init.sql << 'EOF'
-- Инициализация базы данных
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Создание таблицы каналов
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    username VARCHAR(255) UNIQUE,
    description TEXT,
    subscribers_count INTEGER DEFAULT 0,
    theme VARCHAR(100),
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы связей
CREATE TABLE IF NOT EXISTS connections (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES channels(id),
    target_id INTEGER REFERENCES channels(id),
    connection_type VARCHAR(50),
    strength FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Вставка демо данных
INSERT INTO channels (name, username, description, subscribers_count, theme) VALUES
('Демо канал 1', '@demo1', 'Демонстрационный канал для тестирования', 10000, 'Технологии'),
('Демо канал 2', '@demo2', 'Еще один демо канал', 5000, 'Новости'),
('Демо канал 3', '@demo3', 'Третий демо канал', 15000, 'Политика')
ON CONFLICT (username) DO NOTHING;

-- Создание индексов
CREATE INDEX IF NOT EXISTS idx_channels_theme ON channels(theme);
CREATE INDEX IF NOT EXISTS idx_connections_strength ON connections(strength);
EOF

    # redis/redis.conf
    cat > redis/redis.conf << 'EOF'
bind 0.0.0.0
port 6379
timeout 300
maxmemory 1gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF

    # prometheus/prometheus.yml
    cat > prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'telegram-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
EOF

    print_success "Конфигурационные файлы созданы"
}

create_tests() {
    print_info "Создание тестов..."
    
    # tests/test_api.py
    cat > tests/test_api.py << 'EOF'
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_channels():
    response = client.get("/channels")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
EOF

    # pytest.ini
    cat > pytest.ini << 'EOF'
[tool:pytest]
testpaths = tests
python_files = test_*.py
addopts = -v
EOF

    print_success "Тесты созданы"
}

main() {
    echo "🚀 Автоматическое создание проекта Telegram Analysis"
    echo "=================================================="
    
    create_project_structure
    create_main_files
    create_backend_files
    create_frontend_files
    create_scripts
    create_config_files
    create_tests
    
    # Создание .env файла
    cp .env.example .env
    
    print_success "Проект успешно создан!"
    echo ""
    echo "📁 Перейдите в директорию: cd telegram-analysis"
    echo "⚙️  Отредактируйте .env файл"
    echo "🚀 Запустите установку: ./scripts/install.sh"
    echo ""
    echo "📋 Структура проекта:"
    find telegram-analysis -type f | head -20
    echo "   ... и другие файлы"
}

main "$@"
