# from config import SCHEMA_REGISTRY_CONF
from config_k8s import SCHEMA_REGISTRY_CONF
from confluent_kafka.schema_registry import SchemaRegistryClient

schema_registry_client = SchemaRegistryClient(SCHEMA_REGISTRY_CONF)


def get_versions(subject_name):
    versions = schema_registry_client.get_versions(subject_name)
    return versions


def delete_schema(subject_name, version=None):
    if subject_name in schema_registry_client.get_subjects():
        if version:
            schema_registry_client.delete_version(subject_name, version)  # soft delete
            schema_registry_client.delete_version(
                subject_name, version, permanent=True
            )  # hard delete
        else:
            schema_registry_client.delete_subject(subject_name)
            schema_registry_client.delete_subject(subject_name, permanent=True)
        print("[INFO] Delete schema successfully !!!")
    else:
        print(f"[INFO] Schema {subject_name} not existed !!!")


def get_schema(topic):
    subject_name = f"{topic}-value"
    subjects = schema_registry_client.get_subjects()
    assert subject_name in subjects
    schema_str = schema_registry_client.get_latest_version(
        subject_name
    ).schema.schema_str
    return schema_str


if __name__ == "__main__":
    topic = "merge_metadata_reviews"
    # topic = "review"
    # topic = "metadata"
    subject_name = f"{topic}-value"

    # print(get_schema(subject_name))

    topics = ["review", "metadata", "merge_metadata_reviews"]
    for topic in topics:
        subject_name = f"{topic}-value"
        delete_schema(subject_name)
