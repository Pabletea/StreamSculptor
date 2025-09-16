import os
from minio import Minio

def get_minio_client():
# minio_client.py dentro del contenedor
    endpoint = os.environ.get("MINIO_ENDPOINT", "minio:9000")  # correcto
    access_key = os.environ.get("MINIO_KEY", "minioadmin")
    secret_key = os.environ.get("MINIO_SECRET", "minioadmin")

    # Si el endpoint incluye http:// o https://, quitamos antes de separar host/port
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        scheme, rest = endpoint.split("://")
    else:
        scheme, rest = "http", endpoint

    host_port = rest.split(":")
    host = host_port[0]
    port = int(host_port[1]) if len(host_port) > 1 else 9000

    client = Minio(
        "minio:9000",
        access_key=os.environ.get("MINIO_KEY"),
        secret_key=os.environ.get("MINIO_SECRET"),
        secure=False
    )
    return client
