from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from app.models import ModelTrainer
from app.storage import Storage
from app.logger import log
from jose import jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="passlib")

app = FastAPI(title="MLOps HW1")
trainer = ModelTrainer()
storage = Storage()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"])
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-key")


@app.get("/")
async def root():
    return {"message": "Welcome to MLOps HW1 API. Use /docs for Swagger UI."}

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

class TrainRequest(BaseModel):
    model_type: str
    params: dict
    data: dict

class PredictRequest(BaseModel):
    features: list

@app.post("/token")
async def login():
    token = create_access_token({"sub": "user"})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/train/", response_model=dict, 
dependencies=[Depends(get_current_user)])
async def train_model(request: TrainRequest):
    log.info(f"Training {request.model_type} with {request.params}")
    model = trainer.train(request.model_type, request.data["X"], 
request.data["y"], **request.params)
    storage.save(request.model_type, model)
    return {"model_id": request.model_type, "status": "trained"}

@app.get("/models/", response_model=dict, 
dependencies=[Depends(get_current_user)])
async def list_models():
    log.info("Retrieved available models")
    return {"available_models": list(trainer.models.keys())}

@app.post("/predict/{model_id}", response_model=dict, 
dependencies=[Depends(get_current_user)])
async def predict(model_id: str, request: PredictRequest):
    log.info(f"Predicting with {model_id}")
    model = storage.load(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    prediction = model.predict([request.features])
    return {"prediction": prediction.tolist()}

@app.post("/retrain/{model_id}", response_model=dict, 
dependencies=[Depends(get_current_user)])
async def retrain_model(model_id: str, request: TrainRequest):
    log.info(f"Retraining {model_id}")
    model = storage.load(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    new_model = trainer.train(model_id, request.data["X"], 
request.data["y"], **request.params)
    storage.save(model_id, new_model)
    return {"status": "retrained"}

@app.delete("/delete/{model_id}", response_model=dict, 
dependencies=[Depends(get_current_user)])
async def delete_model(model_id: str):
    log.info(f"Deleting {model_id}")
    if storage.delete(model_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Model not found")

@app.get("/health", response_model=dict)
async def health_check():
    log.info("Health check")
    return {"status": "healthy"}
