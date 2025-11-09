from concurrent import futures
import grpc
from . import model_service_pb2
from . import model_service_pb2_grpc
from .models import ModelTrainer
from .storage import Storage
from .logger import log
import pickle

class ModelService(model_service_pb2_grpc.ModelServiceServicer):
    def __init__(self):
        self.trainer = ModelTrainer()

    def TrainModel(self, request, context):
        log.info(f"TRAIN gRPC {request.name}")
        data = pickle.loads(request.data)
        model = self.trainer.train(request.name, data.X, data.y, 
**dict(request.params))
        Storage.save(request.name, model)
        return model_service_pb2.TrainResponse(status="ok")

    def ListModels(self, request, context):
        log.info("List models gRPC")
        return model_service_pb2.ListResponse(models=["forest", "logreg"])

    def Predict(self, request, context):
        log.info(f"Predict gRPC {request.name}")
        model = Storage.load(request.name)
        if not model:
            context.set_details("Model not found")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return model_service_pb2.PredictResponse()
        pred = model.predict([request.features])[0]
        return model_service_pb2.PredictResponse(pred=pred)
	
    def RetrainModel(self, request, context):
        """Retrain an existing model."""
        log.info(f"RETRAIN gRPC {request.model_id}")
        model = Storage.load(request.model_id)
        if not model:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return app.model_service_pb2.TrainResponse(status="not found")
        data = pickle.loads(request.data)
        model_type = Storage.load_metadata().get(request.model_id, {}).get("type", "logreg")
        new_model = self.trainer.train(model_type, data["X"], data["y"], **dict(request.params))
        Storage.save(request.model_id, new_model, model_type, dict(request.params))
        return app.model_service_pb2.TrainResponse(status="retrained")

    def DeleteModel(self, request, context):
        """Delete a trained model."""
        log.info(f"DELETE gRPC {request.model_id}")
        if Storage.delete(request.model_id):
            return app.model_service_pb2.TrainResponse(status="deleted")
        context.set_code(grpc.StatusCode.NOT_FOUND)
        return app.model_service_pb2.TrainResponse(status="not found")

    def Health(self, request, context):
        """Check the health status of the service."""
        log.info("Health check gRPC")
        return app.model_service_pb2.TrainResponse(status="healthy")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    model_service_pb2_grpc.add_ModelServiceServicer_to_server(ModelService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
