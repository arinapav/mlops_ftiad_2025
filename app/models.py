import subprocess
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
import os
import time
from app.logger import log

# Правильный импорт для DVC 3.x
try:
    from dvc.api import DVCFileSystem
    fs = DVCFileSystem(".")
except ImportError:
    log.error("DVC не установлен")
    raise

class ModelTrainer:
    def __init__(self):
        self.models = {
            "forest": RandomForestClassifier,
            "logreg": LogisticRegression
        }
        mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow:5000'))

    def save_and_version_dataset(self, X, y, dataset_name="data"):
        df = pd.DataFrame(X)
        df['target'] = y
        path = f"datasets/{dataset_name}.csv"
        df.to_csv(path, index=False)
        try:
            subprocess.run(["dvc", "add", path], check=True)
            subprocess.run(["git", "add", f"{path}.dvc"], check=True)
            subprocess.run(["git", "commit", "-m", f"Add dataset {dataset_name}"], check=True)
            subprocess.run(["dvc", "push"], check=True)
            log.info(f"Датасет {dataset_name} заверсионирован")
        except subprocess.CalledProcessError as e:
            log.error(f"DVC error: {e}")

    def load_dataset(self, dataset_name="data"):
        path = f"datasets/{dataset_name}.csv"
        try:
            subprocess.run(["dvc", "pull", f"{path}.dvc"], check=True)
            df = pd.read_csv(path)
            X = df.drop('target', axis=1).values
            y = df['target'].values
            return X, y
        except Exception as e:
            log.error(f"Ошибка загрузки датасета: {e}")
            raise

    def train(self, name: str, X=None, y=None, dataset_name="data", **params):
        if name not in self.models:
            raise ValueError("Нет такой модели")

        if X is not None and y is not None:
            self.save_and_version_dataset(X, y, dataset_name)

        X, y = self.load_dataset(dataset_name)

        with mlflow.start_run(run_name=name):
            model_class = self.models[name]
            model = model_class(**params)
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
            model.fit(X_train, y_train)
            acc = accuracy_score(y_test, model.predict(X_test))
            mlflow.log_metric("accuracy", acc)
            mlflow.log_params(params)
            mlflow.sklearn.log_model(model, "model")
            log.info(f"Модель {name} обучена, accuracy: {acc}")
            return model
