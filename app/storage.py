import pickle
import os
from pathlib import Path

Path("models").mkdir(exist_ok=True)

class Storage:
    @staticmethod
    def save(name: str, model):
        with open(f"models/{name}.pkl", "wb") as f:
            pickle.dump(model, f)

    @staticmethod
    def load(name: str):
        try:
            with open(f"models/{name}.pkl", "rb") as f:
                return pickle.load(f)
        except:
            return None

    @staticmethod
    def delete(name: str):
        try:
            os.remove(f"models/{name}.pkl")
            return True
        except:
            return False
