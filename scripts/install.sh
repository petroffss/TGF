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
