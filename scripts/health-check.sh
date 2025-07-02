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
