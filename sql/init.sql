-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Создание индексов для полнотекстового поиска
CREATE INDEX IF NOT EXISTS idx_posts_text_gin ON posts USING gin(to_tsvector('russian', text));
CREATE INDEX IF NOT EXISTS idx_channels_name_gin ON channels USING gin(to_tsvector('russian', name));

-- Создание функции для обновления last_updated
CREATE OR REPLACE FUNCTION update_last_updated_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Создание триггеров
CREATE TRIGGER update_channels_last_updated
    BEFORE UPDATE ON channels
    FOR EACH ROW
    EXECUTE FUNCTION update_last_updated_column();

-- Создание пользователя для мониторинга
CREATE USER monitoring_user WITH PASSWORD 'monitoring_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring_user;

-- Начальные данные
INSERT INTO channels (name, username, description, theme) VALUES
('Демо канал 1', '@demo1', 'Демонстрационный канал для тестирования', 'Технологии'),
('Демо канал 2', '@demo2', 'Еще один демо канал', 'Новости')
ON CONFLICT (username) DO NOTHING;
