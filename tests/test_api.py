"""
Тесты для REST API.
"""
import pytest
from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)


@pytest.fixture
def auth_token():
    """Получение токена авторизации."""
    response = client.post("/token")
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Заголовки с авторизацией."""
    return {"Authorization": f"Bearer {auth_token}"}


def test_root():
    """Тест корневого эндпоинта."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    """Тест health check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_token():
    """Тест получения токена."""
    response = client.post("/token")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


def test_list_models(auth_headers):
    """Тест получения списка моделей."""
    response = client.get("/models/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "available_models" in data
    assert "forest" in data["available_models"]
    assert "logreg" in data["available_models"]


def test_train_model_forest(auth_headers):
    """Тест обучения RandomForest."""
    train_data = {
        "model_type": "forest",
        "params": {
            "n_estimators": 10,
            "max_depth": 3
        },
        "data": {
            "X": [
                [5.1, 3.5, 1.4, 0.2],
                [4.9, 3.0, 1.4, 0.2],
                [7.0, 3.2, 4.7, 1.4],
                [6.4, 3.2, 4.5, 1.5]
            ],
            "y": [0, 0, 1, 1]
        }
    }
    
    response = client.post("/train/", json=train_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == "forest"
    assert data["status"] == "trained"


def test_train_model_logreg(auth_headers):
    """Тест обучения LogisticRegression."""
    train_data = {
        "model_type": "logreg",
        "params": {
            "max_iter": 100
        },
        "data": {
            "X": [
                [5.1, 3.5, 1.4, 0.2],
                [4.9, 3.0, 1.4, 0.2],
                [7.0, 3.2, 4.7, 1.4],
                [6.4, 3.2, 4.5, 1.5]
            ],
            "y": [0, 0, 1, 1]
        }
    }
    
    response = client.post("/train/", json=train_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == "logreg"
    assert data["status"] == "trained"


def test_predict(auth_headers):
    """Тест предсказания."""
    # Обучение модели
    train_data = {
        "model_type": "forest",
        "params": {"n_estimators": 10},
        "data": {
            "X": [
                [5.1, 3.5, 1.4, 0.2],
                [4.9, 3.0, 1.4, 0.2],
                [7.0, 3.2, 4.7, 1.4],
                [6.4, 3.2, 4.5, 1.5]
            ],
            "y": [0, 0, 1, 1]
        }
    }
    client.post("/train/", json=train_data, headers=auth_headers)
    
    # Теперь предсказание
    predict_data = {"features": [5.5, 3.0, 1.5, 0.3]}
    response = client.post(
        "/predict/forest",
        json=predict_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert isinstance(data["prediction"], list)


def test_predict_nonexistent_model(auth_headers):
    """Тест предсказания с несуществующей моделью."""
    predict_data = {"features": [5.5, 3.0, 1.5, 0.3]}
    response = client.post(
        "/predict/nonexistent",
        json=predict_data,
        headers=auth_headers
    )
    assert response.status_code == 404


def test_retrain_model(auth_headers):
    """Тест переобучения модели."""
    # Обучение модели
    train_data = {
        "model_type": "forest",
        "params": {"n_estimators": 10},
        "data": {
            "X": [[5.1, 3.5, 1.4, 0.2], [4.9, 3.0, 1.4, 0.2]],
            "y": [0, 0]
        }
    }
    client.post("/train/", json=train_data, headers=auth_headers)
    
    # Переобучение
    retrain_data = {
        "model_type": "forest",
        "params": {"n_estimators": 20},
        "data": {
            "X": [[7.0, 3.2, 4.7, 1.4], [6.4, 3.2, 4.5, 1.5]],
            "y": [1, 1]
        }
    }
    response = client.post(
        "/retrain/forest",
        json=retrain_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "retrained"


def test_delete_model(auth_headers):
    """Тест удаления модели."""
    # Обучение модели
    train_data = {
        "model_type": "forest",
        "params": {"n_estimators": 10},
        "data": {
            "X": [[5.1, 3.5, 1.4, 0.2], [4.9, 3.0, 1.4, 0.2]],
            "y": [0, 0]
        }
    }
    client.post("/train/", json=train_data, headers=auth_headers)
    
    # Удаляем
    response = client.delete("/delete/forest", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"


def test_unauthorized_access():
    """Тест доступа без токена."""
    response = client.get("/models/")
    assert response.status_code == 401
