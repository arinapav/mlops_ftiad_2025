echo "Creating MinIO buckets..."

# Ждём MinIO
while ! curl -s http://minio:9000/minio/health/live > /dev/null; do
  echo "Waiting for MinIO..."
  sleep 2
done

# Создаём бакеты
for bucket in models datasets mlflow-artifacts; do
  if ! curl -s http://minio:9000/${bucket} > /dev/null 2>&1; then
    echo "Creating bucket: ${bucket}"
    curl -X PUT http://minio:9000/${bucket} -H "x-amz-acl: private"
  else
    echo "Bucket ${bucket} already exists"
  fi
done

echo "Buckets created successfully"
