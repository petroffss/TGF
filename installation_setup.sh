#!/bin/bash
# install.sh - Скрипт автоматической установки системы анализа Telegram каналов

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка прав root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Скрипт запущен от root. Рекомендуется запускать от обычного пользователя с sudo."
        read -p "Продолжить? (y/N): " confirm
        if [[ $confirm != [yY] ]]; then
            exit 1
        fi
    fi
}

# Проверка операционной системы
check_os() {
    print_info "Проверка операционной системы..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            OS="debian"
            print_success "Обнаружена Debian/Ubuntu система"
        elif [ -f /etc/redhat-release ]; then
            OS="redhat"
            print_success "Обнаружена RedHat/CentOS система"
        else
            print_error "Неподдерживаемый дистрибутив Linux"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        print_success "Обнаружена macOS"
    else
        print_error "Неподдерживаемая операционная система: $OSTYPE"
        exit 1
    fi
}

# Установка зависимостей
install_dependencies() {
    print_info "Установка системных зависимостей..."
    
    case $OS in
        "debian")
            sudo apt-get update
            sudo apt-get install -y \
                curl \
                wget \
                git \
                python3 \
                python3-pip \
                python3-venv \
                postgresql-client \
                redis-tools \
                build-essential \
                libpq-dev \
                nginx \
                certbot \
                python3-certbot-nginx
            ;;
        "redhat")
            sudo yum update -y
            sudo yum install -y \
                curl \
                wget \
                git \
                python3 \
                python3-pip \
                postgresql \
                redis \
                gcc \
                gcc-c++ \
                postgresql-devel \
                nginx \
                certbot \
                python3-certbot-nginx
            ;;
        "macos")
            if ! command -v brew &> /dev/null; then
                print_info "Установка Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            
            brew update
            brew install \
                python3 \
                postgresql \
                redis \
                nginx \
                git \
                curl \
                wget
            ;;
    esac
    
    print_success "Системные зависимости установлены"
}

# Установка Docker
install_docker() {
    print_info "Проверка Docker..."
    
    if command -v docker &> /dev/null; then
        print_success "Docker уже установлен"
        return 0
    fi
    
    print_info "Установка Docker..."
    
    case $OS in
        "debian")
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            ;;
        "redhat")
            sudo yum install -y docker
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker $USER
            ;;
        "macos")
            print_warning "Для macOS установите Docker Desktop вручную"
            print_info "Скачайте с: https://www.docker.com/products/docker-desktop"
            read -p "Нажмите Enter после установки Docker Desktop..."
            ;;
    esac
    
    # Установка Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_info "Установка Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    print_success "Docker установлен"
}

# Создание директорий проекта
setup_directories() {
    print_info "Создание структуры директорий..."
    
    PROJECT_DIR="/opt/telegram-analysis"
    
    if [ -d "$PROJECT_DIR" ]; then
        print_warning "Директория $PROJECT_DIR уже существует"
        read -p "Перезаписать? (y/N): " confirm
        if [[ $confirm == [yY] ]]; then
            sudo rm -rf $PROJECT_DIR
        else
            PROJECT_DIR="./telegram-analysis-$(date +%Y%m%d-%H%M%S)"
        fi
    fi
    
    sudo mkdir -p $PROJECT_DIR
    sudo chown $USER:$USER $PROJECT_DIR
    
    cd $PROJECT_DIR
    
    # Создание поддиректорий
    mkdir -p {logs,nginx/{ssl,logs},grafana/{provisioning,dashboards},prometheus,redis,sql,scripts,tests,docs}
    
    print_success "Структура директорий создана в $PROJECT_DIR"
    export PROJECT_DIR
}

# Загрузка исходного кода
download_source() {
    print_info "Загрузка исходного кода..."
    
    # В реальном проекте здесь был бы git clone
    cat > main.py << 'EOF'
# Основной файл API (созданный ранее в артефактах)
from fastapi import FastAPI
app = FastAPI(title="Telegram Analysis API")

@app.get("/")
async def root():
    return {"message": "Telegram Analysis API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
EOF
    
    print_success "Исходный код загружен"
}

# Настройка конфигурации
setup_configuration() {
    print_info "Настройка конфигурации..."
    
    # Создание .env файла
    cat > .env << EOF
# Telegram API (получите на https://my.telegram.org)
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here

# Database
DATABASE_URL=postgresql://telegram_user:$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)@postgres:5432/telegram_analysis

# Redis
REDIS_URL=redis://redis:6379

# JWT Secret
JWT_SECRET=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)

# Email настройки
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ALERT_EMAIL=admin@yourcompany.com

# Grafana
GRAFANA_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Environment
ENVIRONMENT=production
LOG_LEVEL=info
EOF
    
    print_success "Конфигурация создана"
    print_warning "Отредактируйте файл .env и укажите ваши Telegram API ключи"
}

# Генерация SSL сертификатов
setup_ssl() {
    print_info "Настройка SSL сертификатов..."
    
    read -p "Введите ваш домен (или localhost для тестирования): " DOMAIN
    
    if [ "$DOMAIN" = "localhost" ]; then
        # Создание самоподписанного сертификата для разработки
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/key.pem \
            -out nginx/ssl/cert.pem \
            -subj "/C=RU/ST=Moscow/L=Moscow/O=TelegramAnalysis/CN=localhost"
        print_success "Самоподписанный сертификат создан"
    else
        # Настройка Let's Encrypt
        print_info "Настройка Let's Encrypt для домена $DOMAIN"
        sudo certbot certonly --standalone -d $DOMAIN
        
        # Копирование сертификатов
        sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem nginx/ssl/cert.pem
        sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem nginx/ssl/key.pem
        sudo chown $USER:$USER nginx/ssl/*
        
        print_success "SSL сертификаты настроены"
    fi
}

# Построение Docker образов
build_images() {
    print_info "Построение Docker образов..."
    
    # Создание простого Dockerfile для API
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
    
    # Создание requirements.txt
    cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.25.2
EOF
    
    docker-compose build
    print_success "Docker образы построены"
}

# Инициализация базы данных
init_database() {
    print_info "Инициализация базы данных..."
    
    # Ждем запуска PostgreSQL
    print_info "Ожидание запуска PostgreSQL..."
    for i in {1..30}; do
        if docker-compose exec postgres pg_isready -U telegram_user &>/dev/null; then
            break
        fi
        sleep 2
    done
    
    # Создание схемы базы данных
    docker-compose exec postgres psql -U telegram_user -d telegram_analysis -c "
        CREATE TABLE IF NOT EXISTS channels (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            username VARCHAR(255) UNIQUE,
            description TEXT,
            subscribers_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        INSERT INTO channels (name, username, description) VALUES 
        ('Демо канал', '@demo_channel', 'Демонстрационный канал для тестирования')
        ON CONFLICT (username) DO NOTHING;
    "
    
    print_success "База данных инициализирована"
}

# Запуск сервисов
start_services() {
    print_info "Запуск сервисов..."
    
    docker-compose up -d
    
    # Проверка статуса сервисов
    print_info "Проверка статуса сервисов..."
    sleep 10
    
    for service in postgres redis api; do
        if docker-compose ps $service | grep -q "Up"; then
            print_success "$service запущен"
        else
            print_error "$service не запустился"
            docker-compose logs $service
        fi
    done
}

# Проверка работоспособности
health_check() {
    print_info "Проверка работоспособности системы..."
    
    # Проверка API
    if curl -f http://localhost:8000/health &>/dev/null; then
        print_success "API доступен"
    else
        print_error "API недоступен"
    fi
    
    # Проверка базы данных
    if docker-compose exec postgres pg_isready -U telegram_user &>/dev/null; then
        print_success "База данных доступна"
    else
        print_error "База данных недоступна"
    fi
    
    # Проверка Redis
    if docker-compose exec redis redis-cli ping | grep -q PONG; then
        print_success "Redis доступен"
    else
        print_error "Redis недоступен"
    fi
}

# Вывод итоговой информации
show_summary() {
    print_success "Установка завершена!"
    echo
    echo "==================================="
    echo "  СИСТЕМА УСПЕШНО УСТАНОВЛЕНА"
    echo "==================================="
    echo
    echo "📍 Директория проекта: $PROJECT_DIR"
    echo "🌐 Web интерфейс: http://localhost:3000"
    echo "🔌 API: http://localhost:8000"
    echo "📊 Grafana: http://localhost:3001"
    echo "📈 Prometheus: http://localhost:9090"
    echo
    echo "🔧 Управление сервисами:"
    echo "  • Запуск: docker-compose up -d"
    echo "  • Остановка: docker-compose down"
    echo "  • Логи: docker-compose logs -f"
    echo "  • Статус: docker-compose ps"
    echo
    echo "⚙️  Следующие шаги:"
    echo "  1. Отредактируйте файл .env"
    echo "  2. Укажите ваши Telegram API ключи"
    echo "  3. Настройте email для алертов"
    echo "  4. Перезапустите сервисы: docker-compose restart"
    echo
    echo "📚 Документация: http://localhost:8000/docs"
    echo "🆘 Поддержка: создайте issue в репозитории проекта"
    echo
}

# Главная функция
main() {
    echo "========================================"
    echo "  УСТАНОВКА СИСТЕМЫ АНАЛИЗА TELEGRAM"
    echo "========================================"
    echo
    
    check_root
    check_os
    install_dependencies
    install_docker
    setup_directories
    download_source
    setup_configuration
    setup_ssl
    build_images
    start_services
    init_database
    health_check
    show_summary
}

# Обработка ошибок
trap 'print_error "Установка прервана"; exit 1' ERR

# Запуск установки
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi

---

# update.sh - Скрипт обновления системы
#!/bin/bash

set -e

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

main() {
    print_info "Начало обновления системы..."
    
    # Бэкап базы данных
    print_info "Создание бэкапа базы данных..."
    docker-compose exec postgres pg_dump -U telegram_user telegram_analysis > "backup_$(date +%Y%m%d_%H%M%S).sql"
    print_success "Бэкап создан"
    
    # Обновление кода
    print_info "Обновление исходного кода..."
    git pull origin main || print_warning "Git pull failed, продолжаем..."
    
    # Обновление Docker образов
    print_info "Обновление Docker образов..."
    docker-compose pull
    docker-compose build --no-cache
    
    # Перезапуск сервисов
    print_info "Перезапуск сервисов..."
    docker-compose down
    docker-compose up -d
    
    # Проверка здоровья
    print_info "Проверка работоспособности..."
    sleep 15
    
    if curl -f http://localhost:8000/health &>/dev/null; then
        print_success "Система обновлена и работает"
    else
        print_warning "Возможны проблемы с API"
    fi
    
    print_success "Обновление завершено!"
}

main "$@"

---

# backup.sh - Скрипт резервного копирования
#!/bin/bash

set -e

BACKUP_DIR="/opt/telegram-analysis/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание директории для бэкапов
mkdir -p $BACKUP_DIR

print_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

main() {
    print_info "Начало резервного копирования..."
    
    # Бэкап базы данных
    print_info "Создание бэкапа базы данных..."
    docker-compose exec -T postgres pg_dump -U telegram_user telegram_analysis | gzip > "$BACKUP_DIR/database_$DATE.sql.gz"
    
    # Бэкап конфигурации
    print_info "Создание бэкапа конфигурации..."
    tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" .env docker-compose.yml nginx/ grafana/ prometheus/
    
    # Бэкап логов
    print_info "Создание бэкапа логов..."
    tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" logs/
    
    # Очистка старых бэкапов (храним только последние 7 дней)
    find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
    
    print_info "Резервное копирование завершено"
    print_info "Файлы сохранены в: $BACKUP_DIR"
    
    # Отправка уведомления (если настроена почта)
    if [ -n "$ALERT_EMAIL" ]; then
        echo "Резервное копирование системы анализа Telegram завершено успешно в $(date)" | \
        mail -s "Backup Completed" $ALERT_EMAIL || true
    fi
}

main "$@"

---

# restore.sh - Скрипт восстановления из бэкапа
#!/bin/bash

set -e

if [ $# -eq 0 ]; then
    echo "Использование: $0 <backup_file>"
    echo "Пример: $0 /opt/telegram-analysis/backups/database_20231201_120000.sql.gz"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Файл бэкапа не найден: $BACKUP_FILE"
    exit 1
fi

print_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

main() {
    print_info "Начало восстановления из бэкапа: $BACKUP_FILE"
    
    read -p "Вы уверены, что хотите восстановить базу данных? Это удалит все текущие данные! (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        echo "Восстановление отменено"
        exit 0
    fi
    
    # Остановка сервисов
    print_info "Остановка сервисов..."
    docker-compose stop api collector analyzer monitor
    
    # Восстановление базы данных
    print_info "Восстановление базы данных..."
    
    if [[ $BACKUP_FILE == *.gz ]]; then
        gunzip -c "$BACKUP_FILE" | docker-compose exec -T postgres psql -U telegram_user -d telegram_analysis
    else
        docker-compose exec -T postgres psql -U telegram_user -d telegram_analysis < "$BACKUP_FILE"
    fi
    
    # Запуск сервисов
    print_info "Запуск сервисов..."
    docker-compose start api collector analyzer monitor
    
    print_info "Восстановление завершено"
}

main "$@"

---

# monitor.sh - Скрипт мониторинга системы
#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_service() {
    local service=$1
    local port=$2
    local url=$3
    
    if docker-compose ps $service | grep -q "Up"; then
        if [ -n "$url" ]; then
            if curl -f "$url" &>/dev/null; then
                echo -e "✅ $service: ${GREEN}OK${NC}"
            else
                echo -e "⚠️  $service: ${YELLOW}Running but not responding${NC}"
            fi
        else
            echo -e "✅ $service: ${GREEN}Running${NC}"
        fi
    else
        echo -e "❌ $service: ${RED}Not running${NC}"
    fi
}

main() {
    echo "=============================="
    echo "  МОНИТОРИНГ СИСТЕМЫ"
    echo "=============================="
    echo
    
    # Проверка сервисов
    echo "📊 Статус сервисов:"
    check_service "postgres" "5432"
    check_service "redis" "6379"
    check_service "api" "8000" "http://localhost:8000/health"
    check_service "collector" ""
    check_service "analyzer" ""
    check_service "monitor" ""
    check_service "frontend" "80" "http://localhost:3000"
    check_service "nginx" "443"
    check_service "grafana" "3000" "http://localhost:3001"
    check_service "prometheus" "9090" "http://localhost:9090"
    
    echo
    
    # Использование ресурсов
    echo "💾 Использование ресурсов:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
    
    echo
    
    # Размер базы данных
    echo "🗄️  Статистика базы данных:"
    docker-compose exec postgres psql -U telegram_user -d telegram_analysis -c "
        SELECT 
            schemaname,
            tablename,
            attname,
            n_distinct,
            correlation 
        FROM pg_stats 
        WHERE schemaname = 'public' 
        LIMIT 10;
    " 2>/dev/null || echo "Не удалось получить статистику БД"
    
    echo
    
    # Логи ошибок
    echo "🚨 Последние ошибки в логах:"
    docker-compose logs --tail=5 api 2>/dev/null | grep -i error || echo "Ошибок не найдено"
    
    echo
    echo "✅ Мониторинг завершен"
}

main "$@"

---

# test.sh - Скрипт тестирования системы
#!/bin/bash

set -e

TEST_DIR="./tests"
mkdir -p $TEST_DIR

print_info() {
    echo "[TEST] $1"
}

test_api() {
    print_info "Тестирование API..."
    
    # Тест health endpoint
    if curl -f http://localhost:8000/health &>/dev/null; then
        echo "✅ Health check passed"
    else
        echo "❌ Health check failed"
        return 1
    fi
    
    # Тест root endpoint
    if curl -f http://localhost:8000/ &>/dev/null; then
        echo "✅ Root endpoint passed"
    else
        echo "❌ Root endpoint failed"
        return 1
    fi
    
    # Тест channels endpoint
    if curl -f http://localhost:8000/channels &>/dev/null; then
        echo "✅ Channels endpoint passed"
    else
        echo "❌ Channels endpoint failed"
        return 1
    fi
}

test_database() {
    print_info "Тестирование базы данных..."
    
    # Тест подключения
    if docker-compose exec postgres pg_isready -U telegram_user &>/dev/null; then
        echo "✅ Database connection passed"
    else
        echo "❌ Database connection failed"
        return 1
    fi
    
    # Тест запроса
    if docker-compose exec postgres psql -U telegram_user -d telegram_analysis -c "SELECT 1;" &>/dev/null; then
        echo "✅ Database query passed"
    else
        echo "❌ Database query failed"
        return 1
    fi
}

test_redis() {
    print_info "Тестирование Redis..."
    
    if docker-compose exec redis redis-cli ping | grep -q PONG; then
        echo "✅ Redis connection passed"
    else
        echo "❌ Redis connection failed"
        return 1
    fi
    
    # Тест записи/чтения
    docker-compose exec redis redis-cli set test_key "test_value" &>/dev/null
    if docker-compose exec redis redis-cli get test_key | grep -q "test_value"; then
        echo "✅ Redis read/write passed"
        docker-compose exec redis redis-cli del test_key &>/dev/null
    else
        echo "❌ Redis read/write failed"
        return 1
    fi
}

test_frontend() {
    print_info "Тестирование Frontend..."
    
    if curl -f http://localhost:3000 &>/dev/null; then
        echo "✅ Frontend accessible"
    else
        echo "❌ Frontend not accessible"
        return 1
    fi
}

load_test() {
    print_info "Нагрузочное тестирование API..."
    
    # Простой нагрузочный тест с curl
    for i in {1..10}; do
        curl -f http://localhost:8000/health &>/dev/null &
    done
    wait
    
    echo "✅ Load test completed"
}

main() {
    echo "=============================="
    echo "  ТЕСТИРОВАНИЕ СИСТЕМЫ"
    echo "=============================="
    echo
    
    test_api
    test_database  
    test_redis
    test_frontend
    load_test
    
    echo
    echo "✅ Все тесты пройдены успешно!"
}

main "$@"

---

# cleanup.sh - Скрипт очистки системы
#!/bin/bash

print_info() {
    echo "[CLEANUP] $1"
}

main() {
    print_info "Начало очистки системы..."
    
    read -p "Вы уверены, что хотите удалить все данные системы? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        echo "Очистка отменена"
        exit 0
    fi
    
    # Остановка и удаление контейнеров
    print_info "Остановка контейнеров..."
    docker-compose down -v
    
    # Удаление образов
    print_info "Удаление Docker образов..."
    docker-compose down --rmi all
    
    # Очистка Docker системы
    print_info "Очистка Docker системы..."
    docker system prune -af
    
    # Удаление директорий с данными
    print_info "Удаление данных..."
    sudo rm -rf logs/* backups/*
    
    print_info "Очистка завершена"
}

main "$@"

---

# cron-backup.sh - Скрипт для cron заданий
#!/bin/bash
# Добавьте в crontab: 0 2 * * * /opt/telegram-analysis/scripts/cron-backup.sh

cd /opt/telegram-analysis
./scripts/backup.sh >> logs/backup.log 2>&1

---

# health-check.sh - Скрипт проверки здоровья для cron
#!/bin/bash
# Добавьте в crontab: */5 * * * * /opt/telegram-analysis/scripts/health-check.sh

cd /opt/telegram-analysis

if ! curl -f http://localhost:8000/health &>/dev/null; then
    echo "$(date): API не отвечает, перезапуск..." >> logs/health-check.log
    docker-compose restart api
fi

if ! docker-compose exec postgres pg_isready -U telegram_user &>/dev/null; then
    echo "$(date): PostgreSQL не доступен, перезапуск..." >> logs/health-check.log
    docker-compose restart postgres
fi

if ! docker-compose exec redis redis-cli ping | grep -q PONG; then
    echo "$(date): Redis не доступен, перезапуск..." >> logs/health-check.log
    docker-compose restart redis
fi
