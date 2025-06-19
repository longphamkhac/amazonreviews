# from utils import generate_uuidv7
import uuid_utils as uuid
# from config import *
from config_k8s import *
from minio import Minio
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType


def generate_uuidv7():
    return uuid.uuid7().__str__()


uuidv7_udf = udf(generate_uuidv7, StringType())


def main():
    spark = (
        SparkSession.builder.config(
            "spark.hadoop.fs.s3a.endpoint", f"http://{ENDPOINT}"
        )
        .config("spark.hadoop.fs.s3a.access.key", ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", SECRET_KEY)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .appName("Amazon Reviews batching")
        .getOrCreate()
    )

    minio_client = Minio(
        endpoint=ENDPOINT, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False
    )

    isFound = minio_client.bucket_exists(bucket_name=BUCKET_NAME)
    assert isFound
    df_merge = spark.read.format("delta").load(
        f"s3a://{BUCKET_NAME}/{MERGE_DATA_FOLDER}"
    )
    df_merge = df_merge.withColumn(
        "review_id", uuidv7_udf()
    )  # adding review_id as uuidv7
    df_merge = df_merge.withColumn("time_id", uuidv7_udf())  # adding time_id as uuidv7
    df_merge.createOrReplaceTempView("temp")
    spark.sql(
        """
            SELECT review_id, time_id
            FROM temp
        """
    ).show()
    df_merge.write.format("delta").mode("append").save(
        f"s3a://{BUCKET_NAME}/{REFINED_MERGE_DATA_FOLDER}/"
    )
    print("[INFO] Adding UUIDv7 successfully !!!")


if __name__ == "__main__":
    main()
