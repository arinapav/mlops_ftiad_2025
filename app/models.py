from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression


class ModelTrainer:
    def __init__(self):
        self.models = {
            "forest": RandomForestClassifier,
            "logreg": LogisticRegression
        }

    def train(self, name: str, X, y, **params):
        if name not in self.models:
            raise ValueError("Нет такой модели")
        
        model_class = self.models[name]
        model = model_class(**params)
        return model.fit(X, y)
