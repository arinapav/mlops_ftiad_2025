"""
Тестовый клиент для проверки gRPC сервиса.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import grpc
import pickle
import numpy as np
from app import model_service_pb2
from app import model_service_pb2_grpc


def test_grpc_service():
    """Тестирование gRPC сервиса."""
    
    # Подключение к серверу
    channel = grpc.insecure_channel('localhost:50051')
    stub = model_service_pb2_grpc.ModelServiceStub(channel)
    
    print("=" * 50)
    print("Тестирование gRPC сервиса")
    print("=" * 50)
    
    # Тест 1: Список моделей
    print("\n1. Получение списка доступных моделей...")
    try:
        response = stub.ListModels(model_service_pb2.ListRequest())
        print(f"Доступные модели: {list(response.models)}")
    except grpc.RpcError as e:
        print(f"Ошибка: {e.details()}")
        return
    
    # Тест 2: Обучение модели
    print("\n2. Обучение модели RandomForest...")
    try:
        X = np.array([
            [5.1, 3.5, 1.4, 0.2],
            [4.9, 3.0, 1.4, 0.2],
            [4.7, 3.2, 1.3, 0.2],
            [7.0, 3.2, 4.7, 1.4],
            [6.4, 3.2, 4.5, 1.5],
            [6.9, 3.1, 4.9, 1.5]
        ])
        y = np.array([0, 0, 0, 1, 1, 1])
        
        data = {'X': X, 'y': y}
        serialized_data = pickle.dumps(data)
        
        params = {'n_estimators': 10.0, 'max_depth': 5.0}
        
        request = model_service_pb2.TrainRequest(
            name='forest',
            params=params,
            data=serialized_data
        )
        
        response = stub.TrainModel(request)
        print(f"Статус обучения: {response.status}")
    except grpc.RpcError as e:
        print(f"Ошибка: {e.details()}")
        return
    
    # Тест 3: Предсказание
    print("\n3. Предсказание с помощью обученной модели...")
    try:
        test_features = [5.5, 3.0, 1.5, 0.3]
        request = model_service_pb2.PredictRequest(
            name='forest',
            features=test_features
        )
        
        response = stub.Predict(request)
        print(f"Предсказание для {test_features}: {response.pred}")
    except grpc.RpcError as e:
        print(f"Ошибка: {e.details()}")
        return
    
    print("\n" + "=" * 50)
    print("Все тесты выполнены успешно!")
    print("=" * 50)


if __name__ == '__main__':
    test_grpc_service()
