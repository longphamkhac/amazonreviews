from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType
from minio import Minio
# from config import *
from config_k8s import *
import uuid_utils as uuid

def generate_uuidv7():
    return uuid.uuid7().__str__()
uuidv7_udf = udf(generate_uuidv7, StringType())

def main():
    spark = SparkSession.builder \
        .config("spark.hadoop.fs.s3a.endpoint", f"http://{ENDPOINT}") \
        .config("spark.hadoop.fs.s3a.access.key", ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", SECRET_KEY) \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
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

    isFound = minio_client.bucket_exists(bucket_name=BUCKET_NAME)
    assert isFound

    df_reviews = spark.read.format("delta").load(f"s3a://{BUCKET_NAME}/{DELTA_DATA_FOLDER}/reviews")
    df_reviews.createOrReplaceTempView("raw_reviews")
    df_reviews.show()
    print(f"[INFO] Number of review rows: {df_reviews.count()}")

    df_metadata = spark.read.format("delta").load(f"s3a://{BUCKET_NAME}/{DELTA_DATA_FOLDER}/metadata")
    df_metadata.createOrReplaceTempView("raw_metadata")
    df_metadata.show()
    print(f"[INFO] Number of metadata rows: {df_metadata.count()}")

    ### Merge 2 tables
    df_merge = spark.sql(
        """
            SELECT *, m.parent_product_id AS temp
            FROM raw_reviews r
            INNER JOIN raw_metadata m
            ON r.parent_product_id = m.parent_product_id
        """
    )
    df_merge = df_merge.drop("parent_product_id").withColumnRenamed("temp", "parent_product_id")
    # df_merge = df_merge.withColumn("review_id", uuidv7_udf()) # insert review_id column as UUIDv7
    # df_merge = df_merge.withColumn("time_id", uuidv7_udf()) # insert time_id column as uuidv7
    df_merge.show()

    # df_merge.createOrReplaceTempView("raw_reviews_metadata")
    # spark.sql(
    #     """
    #         SELECT user_id, parent_product_id, rating, category, review_title, store
    #         FROM raw_reviews_metadata
    #         WHERE store IS NOT NULL
    #     """
    # ).show()

    ### Write to delta-format
    df_merge.write.format("delta").mode("append").save(f"s3a://{BUCKET_NAME}/{MERGE_DATA_FOLDER}/")
    print("[INFO] Convert merged data to delta format successfully !!!")

if __name__ == "__main__":
    main()