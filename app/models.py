import subprocess
import pandas as pd
import json
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from dvc.api import add, push, pull
from app.logger import log
import os

class ModelTrainer:
    def __init__(self):
        self.models = {
            "forest": RandomForestClassifier,
            "logreg": LogisticRegression
        }
        mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000'))

    def save_and_version_dataset(self, X, y, dataset_name="data"):
        """Сохраняет датасет в CSV, добавляет в DVC, коммитит версию."""
        df = pd.DataFrame(X)
        df['target'] = y
        df.to_csv(f"datasets/{dataset_name}.csv", index=False)
        try:
            add(f"datasets/{dataset_name}.csv")
            subprocess.run(["git", "add", ".dvc"], check=True)
            subprocess.run(["git", "commit", "-m", f"Version dataset {dataset_name}"], check=True)
            push(repo=".")
            log.info(f"Dataset {dataset_name} versioned in DVC/Minio")
        except subprocess.CalledProcessError as e:
            log.error(f"DVC error: {e}")

    def load_dataset(self, dataset_name="data"):
        """Загружает датасет из DVC."""
        try:
            pull(repo=".")
            df = pd.read_csv(f"datasets/{dataset_name}.csv")
            X = df.drop('target', axis=1).values
            y = df['target'].values
            log.info(f"Dataset {dataset_name} loaded from DVC")
            return X, y
        except Exception as e:
            log.error(f"Error loading dataset: {e}")
            raise

    def train(self, name: str, X=None, y=None, dataset_name="data", **params):
        if name not in self.models:
            raise ValueError("Нет такой модели")

        # Если данные переданы, сохраняем и версионируем как новый датасет
        if X is not None and y is not None:
            self.save_and_version_dataset(X, y, dataset_name)

        # Загружаем данные из DVC
        X, y = self.load_dataset(dataset_name)

        with mlflow.start_run(run_name=name):
            model_class = self.models[name]
            model = model_class(**params)
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
            model.fit(X_train, y_train)
            
            # Логируем в MLflow
            mlflow.log_params(params)
            acc = accuracy_score(y_test, model.predict(X_test))
            mlflow.log_metric("accuracy", acc)
            mlflow.sklearn.log_model(model, "model")
            log.info(f"Model {name} trained and logged to MLflow (acc: {acc})")
            
            return model
