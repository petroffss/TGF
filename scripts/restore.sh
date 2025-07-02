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
