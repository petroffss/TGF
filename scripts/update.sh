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
