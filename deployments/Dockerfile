FROM python:3.12-bullseye

WORKDIR /app

# Копируем весь проект
COPY . /app

# Устанавливаем зависимости
RUN pip install -r /app/deployments/requirements.txt

# Права на выполнение скрипта
RUN chmod +x /app/deployments/deploy.sh

ENTRYPOINT ["sh", "./deployments/deploy.sh"]