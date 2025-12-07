import boto3
import pickle
import io
import os
from botocore.exceptions import ClientError
from app.logger import log

class Storage:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://localhost:9000'),
            aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
            aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        )
        self.bucket = 'models'

    def save(self, name: str, model):
        try:
            buffer = io.BytesIO()
            pickle.dump(model, buffer)
            buffer.seek(0)
            self.s3_client.put_object(Bucket=self.bucket, Key=f"{name}.pkl", Body=buffer)
            log.info(f"Model {name} saved to Minio")
        except ClientError as e:
            log.error(f"Error saving model: {e}")
            raise

    def load(self, name: str):
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=f"{name}.pkl")
            buffer = io.BytesIO(response['Body'].read())
            model = pickle.load(buffer)
            log.info(f"Model {name} loaded from Minio")
            return model
        except ClientError:
            log.warning(f"Model {name} not found in Minio")
            return None

    def delete(self, name: str):
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=f"{name}.pkl")
            log.info(f"Model {name} deleted from Minio")
            return True
        except ClientError:
            log.warning(f"Model {name} not found in Minio")
            return False
