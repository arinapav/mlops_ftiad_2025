# app/storage.py
import boto3
import botocore
import pickle
import io
import os
from botocore.exceptions import ClientError
from app.logger import log

class Storage:
    def __init__(self):
        endpoint = os.getenv('MINIO_ENDPOINT', 'http://minio:9000')
        access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')

        try:
            self.s3 = boto3.client(
                's3',
                endpoint_url=endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=boto3.session.Config(signature_version='s3v4')
            )
            # Простая проверка подключения
            self.s3.list_buckets()
            log.info("Connected to MinIO")
        except Exception as e:
            log.error(f"Cannot connect to MinIO: {e}")
            raise Exception(f"MinIO connection failed: {str(e)}")

        self.bucket = 'models'
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            self.s3.create_bucket(Bucket=self.bucket)
            log.info(f"Bucket {self.bucket} created")
        except ClientError as e:
            if e.response['Error']['Code'] not in ['BucketAlreadyOwnedByYou', 'BucketAlreadyExists']:
                log.warning(f"Could not create bucket: {e}")

    def save(self, name: str, model):
        buffer = io.BytesIO()
        pickle.dump(model, buffer)
        buffer.seek(0)
        self.s3.put_object(Bucket=self.bucket, Key=f"{name}.pkl", Body=buffer)
        log.info(f"Model {name} saved")

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
