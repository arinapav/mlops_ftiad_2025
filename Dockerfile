FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

# Копируем только файлы зависимостей
COPY pyproject.toml poetry.lock ./

# Устанавливаем Poetry и зависимости (только продакшн)
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi

# Копируем код
COPY . .

# Создаём нужные папки
RUN mkdir -p datasets models .dvc

EXPOSE 8000 50051 8501

CMD poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 & \
    poetry run python -m app.grpc_server & \
    poetry run streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0
