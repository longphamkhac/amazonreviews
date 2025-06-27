import os

KAFKA_BOOTSTRAP_SERVER = os.getenv(
    "KAFKA_BOOTSTRAP_SERVER",
    "kafka-kafka-bootstrap.infrastructure.svc.cluster.local:9192",
)
ENDPOINT = os.getenv("ENDPOINT", "minio-svc.infrastructure.svc.cluster.local:9000")
ACCESS_KEY = os.getenv("ACCESS_KEY", "minio_access_key")
SECRET_KEY = os.getenv("SECRET_KEY", "minio_secret_key")
BUCKET_NAME = os.getenv("BUCKET_NAME", "amazonreviews")

RAW_DATA_FOLDER = os.getenv("RAW_DATA_FOLDER", "bronze/historical-raw-data")
DELTA_DATA_FOLDER = os.getenv(
    "DELTA_DATA_FOLDER", "silver/historical-delta-format-data"
)
MERGE_DATA_FOLDER = os.getenv("MERGE_DATA_FOLDER", "silver/historical-merge-data")
STREAMING_DATA_FOLDER = os.getenv("STREAMING_DATA_FOLDER", "gold/streaming-data")
REFINED_MERGE_DATA_FOLDER = os.getenv("REFINED_MERGE_DATA_FOLDER", "gold/merge-data")

NUM_PARTITIONS = os.getenv("NUM_PARTITIONS", 16)

SCHEMA_REGISTRY_ENDPOINT = os.getenv(
    "SCHEMA_REGISTRY_ENDPOINT",
    "http://schema-registry-svc.infrastructure.svc.cluster.local:8081",
)
SCHEMA_REGISTRY_CONF = {"url": SCHEMA_REGISTRY_ENDPOINT}
REVIEW_SCHEMA_TOPIC = os.getenv("REVIEW_SCHEMA_TOPIC", "review")
METADATA_SCHEMA_TOPIC = os.getenv("METADATA_SCHEMA_TOPIC", "metadata")
MERGE_SCHEMA_TOPIC = os.getenv("MERGE_SCHEMA_TOPIC", "merge_metadata_reviews")

BATCH_PROCESSING_TIME = "3 minute"

### Postgres config
WAREHOUSE_DATABASE = os.getenv("WAREHOUSE_DATABASE", "demo")
WAREHOUSE_ENDPOINT = os.getenv(
    "WAREHOUSE_ENDPOINT", "postgres-svc.infrastructure.svc.cluster.local"
)
WAREHOUSE_PORT = os.getenv("WAREHOUSE_PORT", "5432")
WAREHOUSE_USER = os.getenv("WAREHOUSE_USER", "admin")
WAREHOUSE_PASSWORD = os.getenv("WAREHOUSE_PASSWORD", "root")
WAREHOUSE_SCHEMA = os.getenv("WAREHOUSE_SCHEMA", "test")
DATAMART_SCHEMA = os.getenv("WAREHOUSE_SCHEMA", "datamart")