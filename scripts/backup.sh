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
