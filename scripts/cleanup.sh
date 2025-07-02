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
