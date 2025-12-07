import boto3
import botocore
import pickle
import io
import time
import os
from botocore.exceptions import ClientError, EndpointConnectionError
from app.logger import log

class Storage:
    def __init__(self):
        endpoint = os.getenv('MINIO_ENDPOINT', 'http://minio:9000')
        access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')

        # Ждём, пока Minio станет доступен (максимум 60 сек)
        for i in range(60):
            try:
                self.s3 = boto3.client(
                    's3',
                    endpoint_url=endpoint,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    config=boto3.session.Config(signature_version='s3v4')
                )
                self.s3.head_bucket(Bucket='models')
                log.info("Minio подключён")
                break
            except (EndpointConnectionError, ClientError) as e:
                log.warning(f"Minio ещё не готов... ждём {i+1}/60 сек")
                time.sleep(1)
        else:
            log.error("Не удалось подключиться к Minio")
            raise Exception("Minio недоступен")

        self.bucket = 'models'
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            self.s3.create_bucket(Bucket=self.bucket)
            log.info(f"Бакет {self.bucket} создан")
        except ClientError as e:
            if e.response['Error']['Code'] != 'BucketAlreadyOwnedByYou':
                pass

    def save(self, name: str, model):
        buffer = io.BytesIO()
        pickle.dump(model, buffer)
        buffer.seek(0)
        self.s3.put_object(Bucket=self.bucket, Key=f"{name}.pkl", Body=buffer)
        log.info(f"Модель {name} сохранена в Minio")

    def load(self, name: str):
        try:
            obj = self.s3.get_object(Bucket=self.bucket, Key=f"{name}.pkl")
            return pickle.loads(obj['Body'].read())
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise

    def delete(self, name: str):
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=f"{name}.pkl")
            return True
        except:
            return False
