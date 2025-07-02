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
