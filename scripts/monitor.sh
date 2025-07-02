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
