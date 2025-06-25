import uuid_utils as uuid
# from config import *
from config_k8s import *
from create_gold_schema_tables import *
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
        .config("spark.jars.packages", "org.postgresql:postgresql:42.7.3")
        .appName("Amazon Reviews batching")
        .getOrCreate()
    )

    postgres_url = (
        f"jdbc:postgresql://{WAREHOUSE_ENDPOINT}:{WAREHOUSE_PORT}/{WAREHOUSE_DATABASE}"
    )
    minio_client = Minio(
        endpoint=ENDPOINT, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False
    )

    ## Create gold schema
    create_tables()

    isFound = minio_client.bucket_exists(bucket_name=BUCKET_NAME)
    assert isFound

    df_merge = spark.read.format("delta").load(
        f"s3a://{BUCKET_NAME}/{REFINED_MERGE_DATA_FOLDER}"
    )
    df_merge.createOrReplaceTempView("merge_data")

    ## dim_time
    dim_time_query = """
        SELECT 
            time_id,
            timestamp as review_date,
            YEAR(timestamp) as year,
            MONTH(timestamp) as month,
            DAY(timestamp) as day,
            QUARTER(timestamp) as quarter
        FROM merge_data
    """
    dim_time_df = spark.sql(dim_time_query)
    dim_time_df.write.format("jdbc").option("url", postgres_url).option(
        "dbtable", f"{WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.dim_time"
    ).option("user", f"{WAREHOUSE_USER}").option(
        "password", f"{WAREHOUSE_PASSWORD}"
    ).option(
        "driver", "org.postgresql.Driver"
    ).mode(
        "append"
    ).save()
    print("[INFO] Create dim_time table successfully!!!")

    ## dim_reviews
    dim_reviews_text_query = """
        SELECT 
            review_id,
            review_title,
            review_text
        FROM merge_data
    """
    dim_reviews_text_df = spark.sql(dim_reviews_text_query)
    dim_reviews_text_df.write.format("jdbc").option("url", postgres_url).option(
        "dbtable", f"{WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.dim_reviews"
    ).option("user", f"{WAREHOUSE_USER}").option(
        "password", f"{WAREHOUSE_PASSWORD}"
    ).option(
        "driver", "org.postgresql.Driver"
    ).mode(
        "append"
    ).save()
    print("[INFO] Create dim_reviews table successfully!!!")

    ## dim_products
    dim_products_query = """
        SELECT 
            product_id,
            FIRST(parent_product_id) as parent_product_id,
            FIRST(category) as category,
            FIRST(store) as store,
            FIRST(product_title) as product_title,
            FIRST(price) as price,
            FIRST(brand) as brand,
            FIRST(material) as material
        FROM merge_data
        GROUP BY product_id
    """
    dim_products_df = spark.sql(dim_products_query)
    dim_products_df.write.format("jdbc").option("url", postgres_url).option(
        "dbtable", f"{WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.dim_products"
    ).option("user", f"{WAREHOUSE_USER}").option(
        "password", f"{WAREHOUSE_PASSWORD}"
    ).option(
        "driver", "org.postgresql.Driver"
    ).mode(
        "append"
    ).save()
    print("[INFO] Create dim_products table successfully!!!")

    ## fact_reviews
    fact_reviews_query = """
        SELECT 
            review_id, 
            product_id, 
            user_id, 
            time_id, 
            rating, 
            verified_purchase, 
            helpful_vote
        FROM merge_data
    """
    fact_reviews_df = spark.sql(fact_reviews_query)
    fact_reviews_df.write.format("jdbc").option("url", postgres_url).option(
        "dbtable", f"{WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.fact_reviews"
    ).option("user", f"{WAREHOUSE_USER}").option(
        "password", f"{WAREHOUSE_PASSWORD}"
    ).option(
        "driver", "org.postgresql.Driver"
    ).mode(
        "append"
    ).save()
    print("[INFO] Create fact_reviews table successfully!!!")

    print("[INFO] Save gold schema successfully!!!")


if __name__ == "__main__":
    main()
