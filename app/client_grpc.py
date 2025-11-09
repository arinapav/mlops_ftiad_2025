import grpc
import pickle
import numpy as np
from app import model_service_pb2
from app import model_service_pb2_grpc

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = model_service_pb2_grpc.ModelServiceStub(channel)

        # Подготовка реальных данных для forest
        X_forest = np.array([[5.1, 3.5, 1.4, 0.2], [4.9, 3.0, 1.4, 0.2]])
        y_forest = np.array([0, 0])
        data_forest = pickle.dumps({'X': X_forest, 'y': y_forest})

        request_forest = model_service_pb2.TrainRequest(
            name="forest",
            params={"n_estimators": 10, "max_depth": 5},
            data=data_forest
        )
        response_forest = stub.TrainModel(request_forest)
        print(f"Train response for forest: {response_forest.status}")

        # Подготовка реальных данных для logreg
        X_logreg = np.array([[5.1, 3.5, 1.4, 0.2], [4.9, 3.0, 1.4, 0.2]])
        y_logreg = np.array([0, 0])
        data_logreg = pickle.dumps({'X': X_logreg, 'y': y_logreg})

        request_logreg = model_service_pb2.TrainRequest(
            name="logreg",
            params={"max_iter": 100, "C": 1.0},
            data=data_logreg
        )
        response_logreg = stub.TrainModel(request_logreg)
        print(f"Train response for logreg: {response_logreg.status}")

if __name__ == '__main__':
    run()
