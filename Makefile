.PHONY: all install clean
.PHONY: dc-up dc-down mlflow-up mlflow-down init-buckets
.PHONY: dvc-init dvc-pull dvc-push
.PHONY: k8s-up k8s-down k8s-status
.PHONY: full up down

# === Основные ===
install:
	@echo "Установка зависимостей..."
	poetry install --no-interaction

clean:
	@echo "Очистка временных файлов..."
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache .dvc/cache
	rm -f *.log

# === Docker Compose ===
dc-up:
	@echo "Запуск Minio и приложения через docker compose..."
	docker compose up -d --build
	@echo "Ожидание готовности Minio..."
	sleep 20

dc-down:
	@echo "Остановка контейнеров..."
	docker compose down -v

mlflow-up:
	@echo "MLflow уже запущен в основном compose"

mlflow-down:
	docker compose -f docker-compose.mlflow.yml down -v

# === Minio: создание бакетов ===
init-buckets:
	@echo "Creating MinIO buckets..."
	@docker compose exec minio mc alias set local http://localhost:9000 minioadmin minioadmin 2>/dev/null || true
	@docker compose exec minio mc mb local/models --ignore-existing 2>/dev/null || true
	@docker compose exec minio mc mb local/datasets --ignore-existing 2>/dev/null || true
	@docker compose exec minio mc mb local/mlflow-artifacts --ignore-existing 2>/dev/null || true
	@docker compose exec minio mc anonymous set public local/models 2>/dev/null || true
	@echo "MinIO buckets created"
# DVC
dvc-init:
	@echo "Настройка DVC..."
	dvc init --no-scm -f 2>/dev/null || true
	dvc remote add -d minio s3://datasets -f 2>/dev/null || true
	dvc remote modify minio endpointurl http://minio:9000
	dvc remote modify minio access_key_id minioadmin
	dvc remote modify minio secret_access_key minioadmin

dvc-pull:
	dvc pull || echo "Нет данных для pull (это нормально при первом запуске)"

dvc-push:
	dvc push

# === Kubernetes ===
MINIKUBE_PROFILE ?= mlops-hw2

k8s-up:
	@echo "Запуск Minikube и деплоя в Kubernetes..."
	minikube start --profile=$(MINIKUBE_PROFILE) --driver=docker --cpus=4 --memory=8g
	minikube addons enable ingress --profile=$(MINIKUBE_PROFILE)
	kubectl apply -f k8s/
	@echo "Проброс портов..."
	kubectl port-forward svc/app 8000:8000 8501:8501 --address=0.0.0.0 &
	kubectl port-forward svc/minio 9000:9000 9001:9001 --address=0.0.0.0 &
	kubectl port-forward svc/mlflow 5000:5000 --address=0.0.0.0 &

k8s-down:
	minikube stop --profile=$(MINIKUBE_PROFILE) || true
	minikube delete --profile=$(MINIKUBE_PROFILE) || true

# === Весь запуск ===
full: clean install dc-up mlflow-up init-buckets dvc-init dvc-pull
	@echo "============================================"
	@echo "Всё успешно запущено! Доступ:"
	@echo "   API Docs:          http://localhost:8000/docs"
	@echo "   Dashboard:         http://localhost:8501"
	@echo "   Minio Console:     http://localhost:9001 (minioadmin/minioadmin)"
	@echo "   MLflow UI:         http://localhost:5000"
	@echo "   DVC настроен — загружай датасеты через дашборд"
	@echo "============================================"

# Удобные алиасы
up: full
down: dc-down mlflow-down

# === Команды для ДЗ-3 (5 баллов) ===

# 1. Сборка Docker-образа и пуш в Docker Hub
build-and-push:
	@echo "Сборка Docker-образа..."
	docker build -t arinapav/mlops-ftiad-2025:latest -f docker/Dockerfile .
	@echo "Пуш в Docker Hub..."
	docker push arinapav/mlops-ftiad-2025:latest

# 2. Запуск тестов
test:
	@echo "Запуск unit-тестов..."
	poetry run pytest -v

# 3. Запуск линтеров
lint:
	@echo "Запуск линтеров..."
	poetry run flake8 app tests
	poetry run black --check app tests
	poetry run isort --check-only app tests
