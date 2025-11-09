.PHONY: install run test clean stop all

# Установка зависимостей
install:
	@echo "Установка зависимостей..."
	@poetry install || pip install -r requirements.txt

# Запуск всех сервисов в фоне
run:
	@echo "Запуск сервисов..."
	@poetry run uvicorn app.api:app --port 8000 --reload > api.log 2>&1 &
	@echo "REST API запущен на порту 8000"
	@sleep 2
	@poetry run python -m app.grpc_server > grpc.log 2>&1 &
	@echo "gRPC сервер запущен на порту 50051"
	@sleep 2
	@poetry run streamlit run dashboard/app.py --server.port 8501 > dashboard.log 2>&1 &
	@echo "Dashboard запущен на порту 8501"
	@echo "Логи сохраняются в api.log, grpc.log, dashboard.log"
	@echo "Открыть:"
	@echo "   - API Docs: http://localhost:8000/docs"
	@echo "   - Dashboard: http://localhost:8501"
	@sleep 3

# Тестирование
test:
	@echo "Запуск тестов..."
	@poetry run pytest tests/test_api.py -v
	@echo "Тестирование gRPC..."
	@poetry run python tests/grpc_client_test.py

# Остановка всех сервисов
stop:
	@echo "Остановка сервисов..."
	@pkill -f "uvicorn app.api:app" || true
	@pkill -f "app.grpc_server" || true
	@pkill -f "streamlit run" || true
	@echo "Все сервисы остановлены"

# Очистка
clean: stop
	@echo "Очистка..."
	@rm -f *.log
	@rm -rf __pycache__ */__pycache__ */*/__pycache__
	@rm -rf .pytest_cache
	@rm -f models/*.pkl

# Полный цикл: установка -> запуск -> тест -> остановка
all: clean install run test
	@echo "Все тесты пройдены!"
	@echo "Сервисы работают. Используйте 'make stop' для остановки"

# Быстрый запуск и тест
quick: stop run test
	@echo "Готово!"
