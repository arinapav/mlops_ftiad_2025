from concurrent import futures
import grpc
import model_service_pb2
import model_service_pb2_grpc
from app.models import ModelTrainer
from app.storage import Storage
from app.logger import log
import pickle

class ModelService(model_pb2_grpc.ModelServiceServicer):
    def __init__(self):
        self.trainer = ModelTrainer()

    def TrainModel(self, request, context):
        log.info(f"TRAIN gRPC {request.name}")
        data = pickle.loads(request.data)
        model = self.trainer.train(request.name, data.X, data.y, 
**dict(request.params))
        Storage.save(request.name, model)
        return model_pb2.TrainResponse(status="ok")

    def ListModels(self, request, context):
        log.info("List models gRPC")
        return model_pb2.ListResponse(models=["forest", "logreg"])

    def Predict(self, request, context):
        log.info(f"Predict gRPC {request.name}")
        model = Storage.load(request.name)
        if not model:
            context.set_details("Model not found")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return model_pb2.PredictResponse()
        pred = model.predict([request.features])[0]
        return model_pb2.PredictResponse(pred=pred)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    model_pb2_grpc.add_ModelServiceServicer_to_server(ModelService(), 
server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
