.PHONY: build up down logs shell migrate test clean

# Сборка всех сервисов
build:
	docker-compose build

# Запуск всех сервисов
up:
	docker-compose up -d

# Остановка всех сервисов
down:
	docker-compose down

# Просмотр логов
logs:
	docker-compose logs -f

# Подключение к API контейнеру
shell:
	docker-compose exec api bash

# Выполнение миграций
migrate:
	docker-compose exec api alembic upgrade head

# Запуск тестов
test:
	docker-compose exec api pytest

# Очистка системы
clean:
	docker-compose down -v
	docker system prune -af

# Бэкап базы данных
backup:
	docker-compose exec postgres pg_dump -U telegram_user telegram_analysis > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Восстановление из бэкапа
restore:
	@read -p "Enter backup file path: " backup_file; \
	docker-compose exec -T postgres psql -U telegram_user telegram_analysis < $$backup_file

# Мониторинг статуса сервисов
status:
	docker-compose ps

# Просмотр использования ресурсов
stats:
	docker stats

# Обновление системы
update:
	git pull
	docker-compose pull
	docker-compose build
	docker-compose up -d

# Перезапуск конкретного сервиса
restart-api:
	docker-compose restart api

restart-collector:
	docker-compose restart collector

restart-analyzer:
	docker-compose restart analyzer
