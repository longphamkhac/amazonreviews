from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import broadcast
from config_k8s import  *

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
        .appName("Amazon Reviews Merge Job")
        .getOrCreate()
    )

    df_review = spark.read.format("delta").load(
        f"s3a://{BUCKET_NAME}/{DELTA_DATA_FOLDER}/reviews"
    )
    df_metadata = spark.read.format("delta").load(
        f"s3a://{BUCKET_NAME}/{DELTA_DATA_FOLDER}/metadata"
    )

    df_review = (
        df_review
        .select(
            "user_id", "parent_product_id", "product_id", "timestamp", 
            "rating", "helpful_vote", "verified_purchase"
        )
    )

    # ép unique theo key để tránh nhân bản khi join
    df_pproduct_id = (
        df_metadata
        .select("category", "parent_product_id", "brand", "store", "price")
        .dropna(how="all", subset=["brand", "store"])
        .withColumn("brand", F.initcap(F.coalesce(F.col("brand"), F.col("store"))))
        .withColumn("store", F.initcap(F.coalesce(F.col("store"), F.col("brand"))))
        .select("category", "parent_product_id", "brand", "price")
    )

    # ép unique theo key để tránh nhân bản khi join
    df_pproduct_id_keyed = df_pproduct_id.dropDuplicates(["parent_product_id"])

    df_keys = (
        df_review.select("parent_product_id")
        .union(df_pproduct_id_keyed.select("parent_product_id"))
        .distinct()
    )

    df_reviews_agg = (
        df_review
        .groupBy("parent_product_id")
        .agg(
            F.count("*").alias("num_reviews"),
            F.round(F.avg("rating"), 1).alias("avg_rating"),
            F.sum("helpful_vote").alias("num_helpful_votes"),
            F.sum(F.col("verified_purchase").cast("int")).alias("num_sell_products")
        )
    )

    df_sub_products = (
        df_review
        .select("parent_product_id", "product_id")
        .dropDuplicates(["parent_product_id", "product_id"])
        .groupBy("parent_product_id")
        .agg(F.count("*").alias("num_sub_products"))
    )

    df_product_metadata = (
        df_keys
        .join(df_reviews_agg, on="parent_product_id", how="left")
        .join(df_sub_products, on="parent_product_id", how="left")
        # .join(broadcast(df_pproduct_id_keyed), on="parent_product_id", how="left")
        .join(df_pproduct_id_keyed, on="parent_product_id", how="left")
    )

    # df_review.write.format("delta").mode("overwrite").save(
    #     f"s3a://{BUCKET_NAME}/{MERGE_DATA_FOLDER}/reviews"
    # )
    # df_product_metadata.write.format("delta").mode("overwrite").save(
    #     f"s3a://{BUCKET_NAME}/{MERGE_DATA_FOLDER}/metadata"
    # )

    df_review.write.format("delta").mode("overwrite").save(
        f"s3a://{BUCKET_NAME}/{MERGE_DATA_FOLDER}/reviews"
    )
    df_product_metadata.write.format("delta").mode("overwrite").save(
        f"s3a://{BUCKET_NAME}/{MERGE_DATA_FOLDER}/metadata"
    )

    print("[INFO] Push to delta lake successfully !!!")

if __name__ == "__main__":
    main()