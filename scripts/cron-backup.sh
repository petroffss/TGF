#!/bin/bash
# Добавьте в crontab: 0 2 * * * /opt/telegram-analysis/scripts/cron-backup.sh

cd /opt/telegram-analysis
./scripts/backup.sh >> logs/backup.log 2>&1
