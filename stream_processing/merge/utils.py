from confluent_kafka.schema_registry import SchemaRegistryClient, Schema
from config_k8s import *

schema_registry_client = SchemaRegistryClient(SCHEMA_REGISTRY_CONF)

def register_schema(subject_name, schema_path):
    subjects = schema_registry_client.get_subjects()
    if subject_name in subjects:
        print(f"[INFO] Schema {subject_name} already existed !!!")
    else:
        with open(schema_path, "r") as f:
            schema_str = f.read()
        schema = Schema(schema_str, schema_type="AVRO")
        schema_id = schema_registry_client.register_schema(subject_name, schema)
        print(f"[INFO] Register Schema {subject_name} successfully !!!")

def delete_schema(subject_name, version=None):
    if version:
        schema_registry_client.delete_version(subject_name, version) # soft delete
        schema_registry_client.delete_version(subject_name, version, permanent=True) # hard delete
    else:
        schema_registry_client.delete_subject(subject_name)
        schema_registry_client.delete_subject(subject_name, permanent=True)
    print("[INFO] Delete schema successfully !!!")

def get_schema(subject_name):
    subjects = schema_registry_client.get_subjects()
    assert subject_name in subjects
    schema_str = schema_registry_client.get_latest_version(subject_name).schema.schema_str
    return schema_str

if __name__ == "__main__":
    topic = "review"
    subject_name = f"{topic}-value"