# tests/test_storage_mock.py

import io
import pytest
from moto import mock_aws

def test_boto3_client_can_be_created():
    import boto3
    s3 = boto3.client("s3")
    assert s3 is not None


@pytest.fixture
def mock_s3_client():
    """Фикстура с моками S3 (moto) — как просит задание"""
    with mock_aws():
        import boto3
        s3 = boto3.client(
            "s3",
            aws_access_key_id="test",
            aws_secret_access_key="test"
        )
        bucket_name = "models"
        s3.create_bucket(Bucket=bucket_name)
        yield s3, bucket_name


def test_upload_to_s3(mock_s3_client):
    """Проверяем загрузку файла в мокнутый S3"""
    s3_client, bucket_name = mock_s3_client

    content = b"Test model data"
    key = "test_model.pkl"

    s3_client.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=io.BytesIO(content)
    )

    obj = s3_client.get_object(Bucket=bucket_name, Key=key)
    assert obj['ContentLength'] > 0