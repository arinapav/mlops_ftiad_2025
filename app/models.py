import mlflow
import mlflow.sklearn
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import pickle

class ModelTrainer:
    def __init__(self):
        # Настраиваем MLflow
        mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
        mlflow.set_experiment("mlops-hw2")
        
    def load_dataset(self, dataset_name):
        # Простая заглушка - в реальности загружайте данные из DVC
        import numpy as np
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([0, 1, 0])
        return X, y
        
    def train(self, model_type, dataset_name="data", **params):
        try:
            # Начинаем эксперимент в MLflow
            with mlflow.start_run():
                # Логируем параметры
                mlflow.log_params(params)
                mlflow.log_param("model_type", model_type)
                mlflow.log_param("dataset", dataset_name)
                
                # Загружаем данные
                X, y = self.load_dataset(dataset_name)
                
                # Создаем и обучаем модель
                if model_type == "forest":
                    model = RandomForestClassifier(**params)
                elif model_type == "logreg":
                    model = LogisticRegression(**params)
                else:
                    raise ValueError(f"Unknown model type: {model_type}")
                
                model.fit(X, y)
                
                # Логируем метрики
                accuracy = model.score(X, y)
                mlflow.log_metric("accuracy", accuracy)
                
                # Сохраняем модель в MLflow
                mlflow.sklearn.log_model(model, "model")
                
                return model
                
        except Exception as e:
            print(f"Error in training: {e}")
            raise

    @property
    def models(self):
        return {"forest": RandomForestClassifier, "logreg": LogisticRegression}
