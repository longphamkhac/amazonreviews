from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.functions import broadcast
from pyspark import StorageLevel
from config_k8s import *

# ENDPOINT = "localhost:9000"
# ACCESS_KEY = "minio_access_key"
# SECRET_KEY = "minio_secret_key"
BUCKET_NAME = "amazonreviews"
DELTA_DATA_FOLDER = "silver/historical-delta-format-data"
MERGE_DATA_FOLDER = "silver/merge-data"
MART_DATA_FOLDER = "gold/datamarts"

def main():
    spark = (
        SparkSession.builder
        .config(
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
        .appName("Amazon Reviews Datamarts")
        .getOrCreate()
    )

    df_review = spark.read.format("delta").load(
        f"s3a://{BUCKET_NAME}/{MERGE_DATA_FOLDER}/reviews"
    )
    df_metadata = spark.read.format("delta").load(
        f"s3a://{BUCKET_NAME}/{MERGE_DATA_FOLDER}/metadata"
    )

    ### mart_parent_products
    df_mart_pproducts = (
        df_metadata
        .select(
            "parent_product_id", "num_sub_products", "num_reviews", "avg_rating", "num_helpful_votes", "num_sell_products"
        )
    )

    df_mart_pproducts.write.format("delta").mode("overwrite").save(
        f"s3a://{BUCKET_NAME}/{MART_DATA_FOLDER}/mart_parent_products"
    )

    ### mart_brand
    df_mart_brands = (
        df_metadata
        .filter(F.col("brand").isNotNull())
        .groupBy("brand")
        .agg(
            F.sum("num_reviews").alias("num_reviews"),
            F.round(F.avg("avg_rating"), 1).alias("avg_rating"),
            F.sum("num_helpful_votes").alias("num_helpful_votes"),
            F.sum("num_sell_products").alias("num_sell_products")
        )
    )

    df_mart_brands.write.format("delta").mode("overwrite").save(
        f"s3a://{BUCKET_NAME}/{MART_DATA_FOLDER}/mart_brands"
    )

    ### mart_products
    df_mart_products = (
        df_review
        .groupBy("product_id")
        .agg(
            F.count("*").alias("num_reviews"),
            F.round(F.avg("rating"), 1).alias("avg_rating"),
            F.sum("helpful_vote").alias("num_helpful_votes"),
            F.sum(
                F.when(F.col("verified_purchase") == True, 1).otherwise(0)
            ).alias("num_sell_products")
        )
    )

    df_mart_products.write.format("delta").mode("overwrite").save(
        f"s3a://{BUCKET_NAME}/{MART_DATA_FOLDER}/mart_products"
    )

    ### mart_category
    df_mart_categories = (
        df_metadata
        .filter(F.col("category").isNotNull())
        .groupBy("category")
        .agg(
            F.sum("num_reviews").alias("num_reviews"),
            F.round(F.avg("avg_rating"), 1).alias("avg_rating"),
            F.sum("num_helpful_votes").alias("num_helpful_votes"),
            F.sum("num_sell_products").alias("num_sell_products")
        )
    )

    df_mart_categories.write.format("delta").mode("overwrite").save(
        f"s3a://{BUCKET_NAME}/{MART_DATA_FOLDER}/mart_categories"
    )

    ### mart_users
    cnt = (
        df_review
        .filter(F.col("verified_purchase") == True)
        .groupBy("user_id", "parent_product_id")
        .agg(
            F.count("*").alias("num_buy_products")
        )
    )
    top = (
        cnt
        .groupBy("user_id")
        .agg(
            F.max(F.struct(
                F.col("num_buy_products"),
                F.col("parent_product_id")
            )).alias("top"),
            F.sum("num_buy_products").alias("total_buy_products")
        )
        .select(
            "user_id",
            F.col("top.parent_product_id").alias("parent_product_id"),
            F.col("total_buy_products").alias("num_buy_products")
        )
    )
    rank_pproducts = (
        top
        .join(
            df_metadata.select("parent_product_id", "category", "brand"),
            on="parent_product_id",
            how="inner"
        )
        .select(
            "user_id", "num_buy_products",
            F.col("brand").alias("top_brand"),
            F.col("category").alias("top_category")
        )
    )
    df_mart_users = (
        df_review
        .groupBy("user_id")
        .agg(
            F.count("*").alias("num_reviews"),
            F.round(F.avg("rating"), 1).alias("avg_rating"),
            F.sum("helpful_vote").alias("num_helpful_votes"),
        )
        .join(
            rank_pproducts,
            on="user_id",
            how="inner"
        )
    )

    df_mart_users.write.format("delta").mode("overwrite").save(
        f"s3a://{BUCKET_NAME}/{MART_DATA_FOLDER}/mart_users"
    )

    print("[INFO] Save datamart successful !!!")

if __name__ == "__main__":
    main()