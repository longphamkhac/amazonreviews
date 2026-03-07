import json
from config_k8s import *
from minio import Minio
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (BooleanType, FloatType, IntegerType, StringType,
                               StructField, StructType, TimestampType, MapType, DoubleType)
from utils import *

MAPPING = {
    "float": FloatType(),
    "string": StringType(),
    "int": IntegerType(),
    "boolean": BooleanType(),
}

def get_raw_metadata_schema():
    schema = StructType([
        StructField("main_category", StringType(), False),
        StructField("parent_asin", StringType(), False),
        StructField("title", StringType(), False),
        StructField("price", FloatType(), True),
        StructField("store", StringType(), True),
        StructField(
            "details",
            MapType(StringType(), StringType()),
            True
        )
    ])
    return schema

def get_raw_review_schema():
    schema = StructType([
        StructField("user_id", StringType(), False),
        StructField("rating", FloatType(), False),
        StructField("title", StringType(), False),
        StructField("text", StringType(), False),
        StructField("asin", StringType(), False),
        StructField("parent_asin", StringType(), False),
        StructField("timestamp", DoubleType(), True),
        StructField("helpful_vote", IntegerType(), True),
        StructField("verified_purchase", BooleanType(), True)
    ])
    return schema

def avro_to_df_schema(avro_schema):
    schema = StructType()
    for field in avro_schema["fields"]:
        name, type = field["name"], field["type"]
        if name == "timestamp":
            schema.add(StructField(name, TimestampType(), nullable=True))
        else:
            if isinstance(type, list):
                schema.add(StructField(name, MAPPING[type[1]], nullable=True))
            else:
                schema.add(StructField(name, MAPPING[type], nullable=False))
    return schema

def get_avro_schema(topic):
    avro_schema = json.loads(get_schema(topic))
    return avro_schema

def get_json_file():
    data_dict = {}
    data_dict["review"] = []
    data_dict["metadata"] = []

    minio_client = Minio(
        endpoint=ENDPOINT, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False
    )

    isFound = minio_client.bucket_exists(bucket_name=BUCKET_NAME)
    if isFound:
        objects = minio_client.list_objects(
            bucket_name=BUCKET_NAME, prefix=RAW_DATA_FOLDER, recursive=True
        )
        for obj in objects:
            json_file = f"s3a://{BUCKET_NAME}/{obj.object_name}"
            data_dict["metadata"].append(
                json_file
            ) if "metadata" in json_file else data_dict["review"].append(json_file)

    return data_dict

def main():
    spark = (
        SparkSession.builder
        .config(
            "spark.sql.caseSensitive", "true"
        )
        .config(
            "spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension"
        )
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.hadoop.fs.s3a.endpoint", f"http://{ENDPOINT}")
        .config("spark.hadoop.fs.s3a.access.key", ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .appName("Amazon Reviews Raw2Delta Job")
        .getOrCreate()
    )

    data_dict = get_json_file()

    ### Review
    avro_review_schema = get_avro_schema(topic=REVIEW_SCHEMA_TOPIC)
    review_schema = avro_to_df_schema(avro_review_schema) # new schema

    raw_review_schema = get_raw_review_schema() # raw schema
    df_review = spark.read.schema(raw_review_schema).json(data_dict["review"])
    df_review = (
        df_review
        .withColumn(
            "timestamp", F.to_timestamp(F.col("timestamp") / 1000)
        )
        .select(
            "user_id", "rating", "timestamp", 
            "helpful_vote", "verified_purchase",
            F.col("title").alias("review_title"),
            F.col("text").alias("review_text"),
            F.col("asin").alias("product_id"),
            F.col("parent_asin").alias("parent_product_id")
        )
    )
    df_review = df_review.select(
        *[F.col(f.name).cast(f.dataType).alias(f.name) for f in review_schema.fields]
    )
    df_review = (
        df_review
            .filter(
                F.col("user_id").isNotNull() &
                F.col("rating").isNotNull() &
                F.col("review_title").isNotNull() &
                F.col("review_text").isNotNull() &
                F.col("product_id").isNotNull() &
                F.col("parent_product_id").isNotNull()
            )
    )

    ### Metadata
    avro_metadata_schema = get_avro_schema(topic=METADATA_SCHEMA_TOPIC)
    metadata_schema = avro_to_df_schema(avro_metadata_schema)

    raw_metadata_schema = get_raw_metadata_schema()
    df_metadata = spark.read.schema(raw_metadata_schema).json(data_dict["metadata"])
    df_metadata = (
        df_metadata
        .select(
            F.col("main_category").alias("category"),
            F.col("parent_asin").alias("parent_product_id"),
            F.col("title").alias("product_title"),
            "price", "store",
            F.col("details").getItem("Brand").alias("brand"),
            F.col("details").getItem("Material").alias("material"),
            F.col("details").getItem("Style").alias("style"),
            F.col("details").getItem("Color").alias("color")
        )
    )
    df_metadata = df_metadata.select(
        *[F.col(f.name).cast(f.dataType).alias(f.name) for f in metadata_schema.fields]
    )
    df_metadata = (
        df_metadata
            .filter(
                F.col("category").isNotNull() &
                F.col("parent_product_id").isNotNull() &
                F.col("product_title").isNotNull()
            )
    )

    ### Convert to delta format
    df_review.write.format("delta").mode("overwrite").save(
        f"s3a://{BUCKET_NAME}/{DELTA_DATA_FOLDER}/reviews/"
    )
    df_metadata.write.format("delta").mode("overwrite").save(
        f"s3a://{BUCKET_NAME}/{DELTA_DATA_FOLDER}/metadata/"
    )
    print("[INFO] Convert raw data to delta format successfully !!!")

if __name__ == "__main__":
    main()