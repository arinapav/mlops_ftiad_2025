# Домашние задания №1  по курсу MLOps на программе ФТиАД НИУ ВШЭ

Авторы: Арина Павлова, Анастасия Бабурина

## Описание 
Сервис для управления ML-моделями с REST API, gRPC интерфейсом и веб-дашбордом. Позволяет обучать, переобучать, удалять модели и получать предсказания через различные интерфейсы.

## Сруктура проекта
```
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
├── models/                 # Директория для сохранения моделей
├── pyproject.toml          # Зависимости Poetry
├── poetry.lock             # Lock-файл зависимостей
└── Makefile                # Автоматизация команд
```

## Основные компоненты

### REST API (FastAPI)

**Эндпоинты:**

```POST /train/``` - обучение модели

```POST /predict/{model_id}``` - предсказание

```POST /retrain/{model_id}``` - переобучение

```DELETE /delete/{model_id}``` - удаление модели

```GET /models/``` - список доступных моделей

```GET /health``` - проверка статуса сервиса

```POST /token``` - получение JWT токена

### gRPC сервис
**Методы:**

```TrainModel``` - обучение модели

```Predict``` - получение предсказания

```ListModels``` - список моделей

### Streamlit дашборд

Веб-интерфейс для взаимодействия с сервисом:

- Авторизация и получение токена

- Обучение моделей с настройкой гиперпараметров

- Просмотр доступных моделей

- Получение предсказаний

- Управление моделями (удаление, переобучение)

- Мониторинг статуса сервиса


### Поддерживаемые модели

- Random Forest (forest)
- Logistic Regression (logreg)

### Требования
- Python 3.8+
- Poetry (для управления зависимостями)
- Установленные системные зависимости для scikit-learn

### Установка и запуск
1. Клонирование репозитория
```
git clone https://github.com/arinapav/mlops_ftiad_2025
cd mlops_ftiad_2025
```

2. Установка зависимостей

```
make install
```

3. Запуск сервисов
   
- Автоматический запуск всех сервисов ```make all ``` или ```make run```
- Ручной запуск (в отдельных терминалах)

Терминал 1 - REST API:

```
poetry run uvicorn app.api:app --reload --port 8000
```
Терминал 2 - gRPC сервер:

```
poetry run python -m app.grpc_server
```
Терминал 3 - Дашборд:
```
poetry run streamlit run dashboard/app.py
```

### Доступ к сервисам

После запуска сервисы будут доступны по адресам:

REST API Documentation: http://localhost:8000/docs

Streamlit Dashboard: http://localhost:8501

gRPC Server: localhost:50051

### Логирование
Логи приложения сохраняются в файл app.log


