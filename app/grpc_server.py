from concurrent import futures
import grpc
import pickle
from app import model_service_pb2
from app import model_service_pb2_grpc
from app.models import ModelTrainer
from app.storage import Storage
from app.logger import log


class ModelService(model_service_pb2_grpc.ModelServiceServicer):
    """gRPC сервис для работы с моделями."""

    def __init__(self):
        """Инициализация сервиса."""
        retries = 30
        for i in range(retries):
            try:
                self.storage = Storage()
                log.info("Storage initialized successfully")
                break
            except Exception as e:
                if i == retries - 1:  # Последняя попытка
                    log.error(f"Failed to initialize Storage after {retries} attempts: {e}")
                    raise
                log.warning(f"Storage initialization failed (attempt {i+1}/{retries}), retrying...")
                time.sleep(2)
        
        self.trainer = ModelTrainer()

    def TrainModel(self, request, context):
        """
        Обучение модели через gRPC.

        Args:
            request: TrainRequest с данными для обучения
            context: gRPC context

        Returns:
            TrainResponse со статусом
        """
        try:
            log.info(f"TRAIN gRPC {request.name}")
            data = pickle.loads(request.data)
            params = dict(request.params)
            
            if request.name == "forest":
                if 'n_estimators' in params:
                    params['n_estimators'] = int(params['n_estimators'])
                if 'max_depth' in params:
                    params['max_depth'] = int(params['max_depth'])
            elif request.name == "logreg":
                if 'max_iter' in params:
                    params['max_iter'] = int(params['max_iter'])
            trainer = ModelTrainer()
            model = trainer.train(request.name, data['X'] if data else None, data['y']if data else None, "data_grpc", **params)
            self.storage.save(request.name, model)
            return model_service_pb2.TrainResponse(status="ok")
        except Exception as e:
            log.error(f"Training error: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return model_service_pb2.TrainResponse(status="error")

    def ListModels(self, request, context):
        """
        Получение списка доступных моделей.

        Args:
            request: ListRequest (пустой)
            context: gRPC context

        Returns:
            ListResponse со списком моделей
        """
        log.info("List models gRPC")
        models = list(self.trainer.models.keys())
        return model_service_pb2.ListResponse(models=models)

    def Predict(self, request, context):
        """
        Предсказание с помощью обученной модели.

        Args:
            request: PredictRequest с именем модели и признаками
            context: gRPC context

        Returns:
            PredictResponse с предсказанием
        """
        try:
            log.info(f"Predict gRPC {request.name}")
            model = self.storage.load(request.name)
            if not model:
                context.set_details("Model not found")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return model_service_pb2.PredictResponse()
            pred = model.predict([list(request.features)])[0]
            return model_service_pb2.PredictResponse(pred=float(pred))
        except Exception as e:
            log.error(f"Prediction error: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return model_service_pb2.PredictResponse()


def serve():
    """Запуск gRPC сервера."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    model_service_pb2_grpc.add_ModelServiceServicer_to_server(
        ModelService(), server
    )
    server.add_insecure_port('[::]:50051')
    log.info("gRPC server starting on port 50051")
    server.start()
    print("gRPC server started on port 50051")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
