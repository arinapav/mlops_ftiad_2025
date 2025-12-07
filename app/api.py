from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
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

app = FastAPI(title="MLOps HW2")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"])
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-key")

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
    data: dict = None
    dataset_name: str = "data"

class PredictRequest(BaseModel):
    features: list

@app.get("/")
async def root():
    return {"message": "Welcome to MLOps HW2 API"}

@app.post("/token")
async def login():
    token = create_access_token({"sub": "user"})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/train/", response_model=dict, dependencies=[Depends(get_current_user)])
async def train_model(request: TrainRequest):
    trainer = ModelTrainer()      # ← создаём локально
    storage = Storage()           # ← создаём локально
    log.info(f"Training {request.model_type}")

    if request.data:
        X, y = request.data["X"], request.data["y"]
    else:
        X, y = trainer.load_dataset(request.dataset_name or "data")

    model = trainer.train(
        request.model_type,
        X=X if request.data else None,
        y=y if request.data else None,
        dataset_name=request.dataset_name or "data",
        **request.params
    )
    storage.save(request.model_type, model)
    return {"model_id": request.model_type, "status": "trained"}

@app.get("/models/", response_model=dict, dependencies=[Depends(get_current_user)])
async def list_models():
    trainer = ModelTrainer()
    return {"available_models": list(trainer.models.keys())}

@app.post("/predict/{model_id}", response_model=dict, dependencies=[Depends(get_current_user)])
async def predict(model_id: str, request: PredictRequest):
    storage = Storage()
    model = storage.load(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    prediction = model.predict([request.features])[0]
    return {"prediction": int(prediction)}

@app.delete("/delete/{model_id}", response_model=dict, dependencies=[Depends(get_current_user)])
async def delete_model(model_id: str):
    storage = Storage()
    if storage.delete(model_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Model not found")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/dvc/version")
async def get_dvc_version():
    """Получить версию DVC"""
    try:
        result = subprocess.run(
            ["dvc", "--version"],
            capture_output=True,
            text=True,
            cwd="/app"
        )
        return {"version": result.stdout.strip()}
    except Exception as e:
        logger.error(f"Error getting DVC version: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dvc/status")
async def get_dvc_status():
    """Получить статус DVC"""
    try:
        result = subprocess.run(
            ["dvc", "status"],
            capture_output=True,
            text=True,
            cwd="/app"
        )
        return {
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout if result.stdout else result.stderr
        }
    except Exception as e:
        logger.error(f"Error getting DVC status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dvc/commit")
async def commit_to_dvc(commit_message: Optional[str] = "Dataset update via API"):
    """Закоммитить изменения в DVC"""
    try:
        # Проверяем, есть ли изменения
        status_result = subprocess.run(
            ["dvc", "status"],
            capture_output=True,
            text=True,
            cwd="/app"
        )
        
        if "cache:" not in status_result.stdout and "nothing to commit" in status_result.stdout:
            return {"message": "No changes to commit", "status": "info"}
        
        # Коммитим изменения
        commit_result = subprocess.run(
            ["dvc", "commit", "-f"],
            capture_output=True,
            text=True,
            cwd="/app"
        )
        
        if commit_result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"DVC commit failed: {commit_result.stderr}"
            )
        
        # Пушим изменения в удаленный репозиторий
        push_result = subprocess.run(
            ["dvc", "push"],
            capture_output=True,
            text=True,
            cwd="/app"
        )
        
        if push_result.returncode != 0:
            logger.warning(f"DVC push failed: {push_result.stderr}")
        
        return {
            "status": "success",
            "message": "Successfully committed to DVC",
            "commit_output": commit_result.stdout,
            "push_output": push_result.stdout if push_result.returncode == 0 else push_result.stderr
        }
        
    except Exception as e:
        logger.error(f"Error in DVC commit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dvc/add")
async def add_to_dvc(filepath: str):
    """Добавить файл в DVC"""
    try:
        # Проверяем существование файла
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"File {filepath} not found")
        
        # Добавляем файл в DVC
        result = subprocess.run(
            ["dvc", "add", filepath],
            capture_output=True,
            text=True,
            cwd="/app"
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"DVC add failed: {result.stderr}"
            )
        
        # Добавляем .dvc файл в git
        dvc_file = f"{filepath}.dvc"
        if os.path.exists(dvc_file):
            subprocess.run(["git", "add", dvc_file], cwd="/app")
        
        return {
            "status": "success",
            "message": f"File {filepath} added to DVC",
            "output": result.stdout
        }
        
    except Exception as e:
        logger.error(f"Error adding file to DVC: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dvc/config")
async def get_dvc_config():
    """Получить конфигурацию DVC"""
    try:
        # Получаем конфигурацию удаленного репозитория
        result = subprocess.run(
            ["dvc", "remote", "list"],
            capture_output=True,
            text=True,
            cwd="/app"
        )
        
        return {
            "status": "success",
            "remotes": result.stdout.strip().split("\n") if result.stdout else [],
            "config_exists": os.path.exists(".dvc/config")
        }
    except Exception as e:
        logger.error(f"Error getting DVC config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
