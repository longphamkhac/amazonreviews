import os

JARS_PATH = f"{os.getcwd()}/jars"
AVRO_SCHEMA_FOLDER = "schemas/avro"
REVIEW_SCHEMA_PATH = f"{AVRO_SCHEMA_FOLDER}/review_schema.avsc"
METADATA_SCHEMA_PATH = f"{AVRO_SCHEMA_FOLDER}/metadata_schema.avsc"
MERGE_SCHEMA_PATH = f"{AVRO_SCHEMA_FOLDER}/merge_metadata_reviews_schema.avsc"

REVIEW_SUBJECT_NAME = "review-value"
METADATA_SUBJECT_NAME = "metadata-value"
MERGE_SUBJECT_NAME = "merge_metadata_reviews-value"

MERGE_TOPIC = "merge_metadata_reviews"

KAFKA_BOOTSTRAP_SERVERS = "kafka-kafka-bootstrap.infrastructure.svc.cluster.local:9192"
SCHEMA_REGISTRY_CONF = {
    "url": "http://schema-registry-svc.infrastructure.svc.cluster.local:8081"
}
CONSUMER_PROPS = {
    # "bootstrap.servers": "192.168.49.2:32473,192.168.49.2:30769,192.168.49.2:30294", # NodePort
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    "group.id": "flink-consumer-group",
    "auto.offset.reset": "earliest",
}

MERGE_PRODUCER_PROPS = {"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS}

POSTGRES_DB = "demo"
POSTGRES_USER = "admin"
POSTGRES_PASSWORD = "root"
POSTGRES_HOSTNAME = "postgres-svc.infrastructure.svc.cluster.local"
