#!/bin/bash
echo "Setting up DVC..."

# Инициализируем DVC если не инициализирован
if [ ! -d .dvc ]; then
    echo "Initializing DVC..."
    dvc init --no-scm -f
    
    # Настраиваем удаленный репозиторий
    dvc remote add -d minio s3://datasets
    dvc remote modify minio endpointurl http://minio:9000
    dvc remote modify minio access_key_id minioadmin
    dvc remote modify minio secret_access_key minioadmin
fi

# Создаем папку для датасетов
mkdir -p datasets

echo "DVC setup complete"
