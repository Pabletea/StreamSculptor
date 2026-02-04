import os
from minio import Minio

def get_minio_client():
    endpoint = os.environ.get("MINIO_ENDPOINT", "minio:9000")
    access_key = os.environ.get("MINIO_KEY", "minioadmin")
    secret_key = os.environ.get("MINIO_SECRET", "minioadmin")
    
    # Limpiar el endpoint si tiene esquema
    if "://" in endpoint:
        endpoint = endpoint.split("://")[1]
    
    client = Minio(
        endpoint,  # ← usar la variable
        access_key=access_key,
        secret_key=secret_key,
        secure=False
    )
    return client
