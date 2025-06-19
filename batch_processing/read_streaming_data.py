from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType
import json
from datetime import datetime

from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, TimestampType, BooleanType
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField

# from config import *
from config_k8s import *
from utils import *
import uuid_utils as uuid

def generate_uuidv7():
    return uuid.uuid7().__str__()
uuidv7_udf = udf(generate_uuidv7, StringType())

def avro_to_dataframe_schema(avro_schema, mapping):
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

class AvroDeserializerWrapper:
    def __init__(self, schema_registry_conf, topic):
        self.schema_registry_conf = schema_registry_conf
        self.topic = topic
        self.subject_name = f"{topic}-value"
        self.schema_registry_client, self._deserializer, self.schema_str, self.ctx = None, None, None, None

    def get_schema(self):
        assert self.schema_registry_client
        subjects = self.schema_registry_client.get_subjects()
        assert self.subject_name in subjects
        self.schema_str = self.schema_registry_client.get_latest_version(self.subject_name).schema.schema_str

    def get_deserializer(self):
        if self._deserializer is None:
            self.ctx = SerializationContext(self.topic, MessageField.VALUE)
            self.schema_registry_client = SchemaRegistryClient(self.schema_registry_conf)
            self.get_schema()
            self._deserializer = AvroDeserializer(self.schema_registry_client, self.schema_str)
        return self._deserializer
    
    def deserialize(self, record):
        # try:
        #     return self.get_deserializer()(record, self.ctx)
        # except:
        #     print("[INFO] Invalid record !!!")
        #     return None

        raw_dict = self.get_deserializer()(record, self.ctx)
        return raw_dict

def main():
    spark = SparkSession.builder \
        .master("local[*]") \
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

    uuidv7_udf = udf(generate_uuidv7, StringType())

    mapping = {
        "float": FloatType(),
        "string": StringType(),
        "int": IntegerType(),
        "boolean": BooleanType()
    }
    dataframe_schema = avro_to_dataframe_schema(json.loads(get_schema(MERGE_SCHEMA_TOPIC)), mapping)

    deserializer = AvroDeserializerWrapper(
        schema_registry_conf=SCHEMA_REGISTRY_CONF,
        topic=MERGE_SCHEMA_TOPIC
    )

    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", f"{KAFKA_BOOTSTRAP_SERVER}") \
        .option("subscribe", MERGE_SCHEMA_TOPIC) \
        .option("startingOffsets", "earliest") \
        .option("groupIdPrefix", "spark-merge-consumer") \
        .load()

    # kafka_df = kafka_df.select(
    #     from_avro(col("value"), merge_schema_str, {"schema.registry.url": "http://localhost:8081"})
    # )
    # kafka_df.select("key", "value").writeStream \
    #     .format("console") \
    #     .outputMode("append") \
    #     .trigger(processingTime = "5 seconds") \
    #     .start()

    def process(batch_df, batch_id):
        raw_rdd = batch_df.select("key", "value").rdd

        def process_raw(row):
            bytes_value = bytes(row.value) # byte_array to bytes
            value_utf8_decode = bytes_value.decode("utf-8")
            bytes_value = value_utf8_decode.encode("latin1")
            raw_dict = deserializer.deserialize(bytes_value)
            # print(raw_dict)
            # print()

            ### Convert string to timestamp type
            raw_dict["timestamp"] = datetime.strptime(raw_dict["timestamp"], "%Y-%m-%d %H:%M:%S")
            return raw_dict

        transformed_rdd = raw_rdd.map(process_raw).filter(lambda x: x is not None)
        if not transformed_rdd.isEmpty():
            print(f"Batch {batch_id} transformed RDD count: {transformed_rdd.count()}")
            transformed_df = spark.createDataFrame(transformed_rdd, dataframe_schema)
            # transformed_df.write.format("console").mode("append").save()
            transformed_df = transformed_df.withColumn("review_id", uuidv7_udf()) # insert review_id column as UUIDv7
            transformed_df = transformed_df.withColumn("time_id", uuidv7_udf()) # insert time_id column as uuidv7
            transformed_df.write.format("delta").mode("append").save(f"s3a://{BUCKET_NAME}/{STREAMING_DATA_FOLDER}")
            try:
                transformed_df.write.format("delta").mode("append").save(f"s3a://{BUCKET_NAME}/{REFINED_MERGE_DATA_FOLDER}")
            except:
                pass

    kafka_df.writeStream \
        .foreachBatch(process) \
        .option("checkpointLocation", f"s3a://{BUCKET_NAME}/checkpoints/{STREAMING_DATA_FOLDER}") \
        .trigger(processingTime = f"{BATCH_PROCESSING_TIME}") \
        .start() \
        .awaitTermination()

if __name__ == "__main__":
    main()
