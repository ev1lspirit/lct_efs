FROM python:3.12-bullseye

WORKDIR /app

# Копируем requirements.txt
COPY deployments/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Копируем все директории проекта
COPY adapters /app/adapters
COPY api /app/api
COPY database /app/database
COPY diagrams /app/diagrams
COPY fsm /app/fsm
#COPY Scripts /app/Scripts
COPY storage /app/storage
COPY workflow_builder /app/workflow_builder

# Копируем файлы из корня
COPY config.py /app/config.py
COPY context.py /app/context.py
COPY main.py /app/main.py
COPY utils.py /app/utils.py

# Копируем .env файл
COPY .env /app/.env

# Копируем деплой скрипт
COPY deployments/deploy.sh /app/deployments/deploy.sh
RUN chmod +x /app/deployments/deploy.sh

ENTRYPOINT ["sh", "./deployments/deploy.sh"]