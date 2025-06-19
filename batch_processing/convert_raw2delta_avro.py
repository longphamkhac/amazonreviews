import json
from pyspark.sql import SparkSession
from minio import Minio
from datetime import datetime
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import SerializationContext, MessageField
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, TimestampType, BooleanType

# from config import *
from config_k8s import *
from utils import *

mapping = {
    "float": FloatType(),
    "string": StringType(),
    "int": IntegerType(),
    "boolean": BooleanType()
}

class AvroSerializerWrapper:
    def __init__(self, schema_registry_conf, topic):
        self.schema_registry_conf = schema_registry_conf
        self.topic = topic
        self.subject_name = f"{topic}-value"
        self.schema_registry_client, self._serializer, self.schema_str, self.ctx = None, None, None, None

    def get_schema(self):
        assert self.schema_registry_client
        subjects = self.schema_registry_client.get_subjects()
        assert self.subject_name in subjects
        self.schema_str = self.schema_registry_client.get_latest_version(self.subject_name).schema.schema_str

    def get_serializer(self):
        if self._serializer is None:
            self.ctx = SerializationContext(self.topic, MessageField.VALUE)
            self.schema_registry_client = SchemaRegistryClient(self.schema_registry_conf)
            self.get_schema()
            self._serializer = AvroSerializer(self.schema_registry_client, self.schema_str)
        return self._serializer
    
    def serialize(self, record):
        try:
            self.get_serializer()(record, self.ctx)
            return True
        except:
            # print("[INFO] Invalid record !!!")
            return False

def avro_to_dataframe_schema(avro_schema):
    schema = StructType()
    for field in avro_schema["fields"]:
        name, type = field["name"], field["type"]
        if name == "timestamp":
            schema.add(StructField(name, TimestampType(), nullable=True))
        else:
            if isinstance(type, list):
                schema.add(StructField(name, mapping[type[1]], nullable=True))
            else:
                schema.add(StructField(name, mapping[type], nullable=False))
    return schema

review_serializer_wrapper = AvroSerializerWrapper(
    schema_registry_conf=SCHEMA_REGISTRY_CONF,
    topic=REVIEW_SCHEMA_TOPIC
)

def process_review_feature(record):
    record = json.loads(record)
    processed_record = {
        "user_id": record.get("user_id", None),
        "rating": record.get("rating", None),
        "review_title": record.get("title", None),
        "review_text": record.get("text", None),
        "product_id": record.get("asin", None),
        "parent_product_id": record.get("parent_asin", None),
        "timestamp": str(record.get("timestamp", None)),
        "helpful_vote": record.get("helpful_vote", None),
        "verified_purchase": record.get("verified_purchase", None)
    }
    if review_serializer_wrapper.serialize(processed_record):
        dt_object = datetime.fromtimestamp(int(record["timestamp"]) // 1000.0)
        converted_timestamp = datetime.strptime(dt_object.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
        processed_record["timestamp"] = converted_timestamp
        return processed_record
    return None

metadata_serializer_wrapper = AvroSerializerWrapper(
    schema_registry_conf=SCHEMA_REGISTRY_CONF,
    topic=METADATA_SCHEMA_TOPIC
)

def process_metadata_feature(record):
    record = json.loads(record)
    processed_record = {
        "category": record.get("main_category", None),
        "parent_product_id": record.get("parent_asin", None),
        "product_title": record.get("title", None),
        "price": record.get("price", None),
        "store": record.get("store", None),
        "brand": record["details"].get("brand", None),
        "material": record["details"].get("meterial", None),
        "style": record["details"].get("style", None),
        "color": record["details"].get("color", None)
    }
    if metadata_serializer_wrapper.serialize(processed_record):
        return processed_record
    return None

def main():
    spark = SparkSession.builder \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.hadoop.fs.s3a.endpoint", f"http://{ENDPOINT}") \
        .config("spark.hadoop.fs.s3a.access.key", ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", SECRET_KEY) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .appName("Amazon Reviews batching") \
        .getOrCreate()

    minio_client = Minio(
        endpoint=ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False
    )

    data_dict = {}
    data_dict["reviews"] = []
    data_dict["metadata"] = []

    isFound = minio_client.bucket_exists(bucket_name=BUCKET_NAME)
    if isFound:
        objects = minio_client.list_objects(
            bucket_name=BUCKET_NAME, prefix=RAW_DATA_FOLDER, recursive=True
        )
        for obj in objects:
            json_file = f"s3a://{BUCKET_NAME}/{obj.object_name}"
            data_dict["metadata"].append(json_file) if "metadata" in json_file else data_dict["reviews"].append(json_file)

    ### Review data type
    avro_reviews_schema = json.loads(get_schema(topic=REVIEW_SCHEMA_TOPIC))
    df_reviews_schema = avro_to_dataframe_schema(avro_reviews_schema)
    rdd_reviews = spark.sparkContext.textFile(",".join(data_dict["reviews"]))
    rdd_reviews = rdd_reviews.map(process_review_feature).filter(lambda x: x is not None)
    df_reviews = spark.createDataFrame(rdd_reviews, df_reviews_schema)
    df_reviews.show()
    print(f"[INFO] Number of review rows: {df_reviews.count()}")

    ### Metadata data type
    avro_metadata_schema = json.loads(get_schema(topic=METADATA_SCHEMA_TOPIC))
    df_metadata_schema = avro_to_dataframe_schema(avro_metadata_schema)
    rdd_metadata = spark.sparkContext.textFile(",".join(data_dict["metadata"]))
    rdd_metadata = rdd_metadata.map(process_metadata_feature).filter(lambda x: x is not None)
    df_metadata = spark.createDataFrame(rdd_metadata, df_metadata_schema)
    df_metadata.printSchema()
    df_metadata.show()
    print(f"[INFO] Number of metadata rows: {df_metadata.count()}")

    ### Convert to delta format
    df_reviews.write.format("delta").mode("overwrite").save(f"s3a://{BUCKET_NAME}/{DELTA_DATA_FOLDER}/reviews/")
    df_metadata.write.format("delta").mode("overwrite").save(f"s3a://{BUCKET_NAME}/{DELTA_DATA_FOLDER}/metadata/")

    print("[INFO] Convert raw data to delta format successfully !!!")

if __name__ == "__main__":
    main()
