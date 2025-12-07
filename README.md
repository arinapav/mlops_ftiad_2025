# Домашние задания №1–2 по курсу MLOps на программе ФТиАД НИУ ВШЭ

Авторы: Арина Павлова, Анастасия Бабурина

## Описание

Сервис для управления ML‑моделями с REST API, gRPC интерфейсом и веб‑дашбордом.  
Во 2‑й части добавлены: хранение данных и моделей в S3‑совместимом хранилище Minio, версионирование датасетов с помощью DVC, трекинг экспериментов в MLflow, запуск через Docker Compose и деплой в Kubernetes (Minikube).

## Структура проекта

```bash
mlops_ftiad_2025/
├── app/                    # Основное приложение
│   ├── api.py              # REST API на FastAPI
│   ├── grpc_server.py      # gRPC сервер
│   ├── client_grpc.py      # gRPC клиент для тестирования
│   ├── models.py           # Классы для обучения моделей
│   ├── storage.py          # Хранение и загрузка моделей
│   ├── logger.py           # Настройка логирования
│   └── model_service.proto # gRPC спецификация
├── dashboard/
│   └── app.py              # Streamlit дашборд
├── tests/                  # Тесты
│   ├── test_api.py         # Тесты REST API
│   └── grpc_client_test.py # Тесты gRPC
├── models/                 # Локальная директория для моделей
├── docker-compose.yml      # Minio + MLflow + приложение
├── k8s/                    # Манифесты для деплоя в Kubernetes (Minikube)
├── pyproject.toml          # Зависимости Poetry
├── poetry.lock             # Lock-файл зависимостей
└── Makefile                # Автоматизация команд (Docker, DVC, Kubernetes)
```

## Основные компоненты

### REST API (FastAPI)

**Эндпоинты:**

- `POST /train/` — обучение модели  
- `POST /predict/{model_id}` — предсказание  
- `POST /retrain/{model_id}` — переобучение  
- `DELETE /delete/{model_id}` — удаление модели  
- `GET /models/` — список доступных моделей  
- `GET /health` — проверка статуса сервиса  
- `POST /token` — получение JWT‑токена  

### gRPC сервис

**Методы:**

- `TrainModel` — обучение модели  
- `Predict` — получение предсказания  
- `ListModels` — список моделей  

### Streamlit дашборд

Веб‑интерфейс для взаимодействия с сервисом:

- Авторизация и получение токена  
- Загрузка CSV‑датасета, версионирование в DVC и загрузка в Minio (`datasets` бакет) [1]
- Обучение моделей с настройкой гиперпараметров  
- Просмотр доступных моделей и получение предсказаний  
- Управление моделями (удаление, переобучение)  
- Ссылки на Minio Console и MLflow UI  

## Инфраструктура ДЗ‑2

### Minio + DVC + S3‑хранилище

- Minio развёрнут как сервис в `docker-compose.yml` и используется как S3‑совместимое хранилище  
- DVC настроен на удалённый remote `s3://datasets` в Minio и используется для версионирования датасетов (инициализация и настройка — через таргет `make dvc-init`)

### MLflow

- MLflow сервер развёрнут в Docker Compose и использует Minio как artifact store (`s3://mlflow-artifacts`)
- Приложение логирует эксперименты (модели, метрики, артефакты) в MLflow, трекинг‑сервер доступен через MLflow UI.  

### Docker Compose

- Единый `docker-compose.yml` поднимает три сервиса: `minio`, `mlflow`, `app` (FastAPI + gRPC + Streamlit)
- В `Makefile` предусмотрены таргеты:
  - `make dc-up` — поднять стек Minio + MLflow + приложение в Docker  
  - `make dc-down` — остановить и удалить контейнеры  
  - `make init-buckets` — создать бакеты в Minio (`models`, `datasets`, `mlflow-artifacts`)
  - `make dvc-init`, `make dvc-pull`, `make dvc-push` — работа с DVC‑remote  

### Kubernetes (Minikube)

- В каталоге `k8s/` лежат черновики для деплоя приложения, Minio и MLflow в кластер Minikube   
- В `Makefile` есть таргеты:
  - `make k8s-up` — старт Minikube, применение манифестов и проброс портов (8000, 8501, 9000, 9001, 5000) 
  - `make k8s-down` — остановка и удаление Minikube‑кластера  

## Поддерживаемые модели

- Random Forest (`forest`)  
- Logistic Regression (`logreg`)  

## Требования (локальный запуск без Docker)

- Python 3.8+  
- Poetry (для управления зависимостями)  
- Установленные системные зависимости для `scikit-learn`  

## Установка и запуск

### Вариант 1: через Docker Compose (рекомендуется для ДЗ‑2)

1. Клонировать репозиторий:
   ```bash
   git clone https://github.com/arinapav/mlops_ftiad_2025
   cd mlops_ftiad_2025
   ```

2. Запустить стек:
   ```bash
   make dc-up
   make init-buckets
   make dvc-init

   или

   make full
   ```

3. Доступ к сервисам:
   - REST API Docs:    http://localhost:8000/docs  
   - Streamlit Dashboard: http://localhost:8501  
   - Minio Console:    http://localhost:9001 (логин/пароль: `minioadmin` / `minioadmin`)  
   - MLflow UI:        http://localhost:5000  

### Вариант 2: локальный запуск (без Docker)

1. Установка зависимостей:
   ```bash
   make install
   ```

2. Запуск сервисов в отдельных терминалах:

   Терминал 1 — REST API:
   ```bash
   poetry run uvicorn app.api:app --reload --port 8000
   ```

   Терминал 2 — gRPC сервер:
   ```bash
   poetry run python -m app.grpc_server
   ```

   Терминал 3 — Streamlit дашборд:
   ```bash
   poetry run streamlit run dashboard/app.py --server.port 8501
   ```

## Логирование

- Логи приложения сохраняются в файл `app.log`.  
- Дополнительно параметры обучения и метрики сохраняются в MLflow (через трекинг‑сервер, поднятый в Docker Compose).
