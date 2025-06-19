import uuid_utils as uuid
# from config import *
from config_k8s import *
from create_tables import *
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

    ## dim_users
    dim_users_query = """
        WITH user_buy_products AS (
            SELECT user_id, COUNT(*) as buy_count
            FROM merge_data
            WHERE verified_purchase = true
            GROUP BY user_id
        ),
        user_top_category AS (
            SELECT user_id, category, category_count,
                ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY category_count DESC) as rn
            FROM (
                SELECT user_id, category, COUNT(*) as category_count
                FROM merge_data
                GROUP BY user_id, category
            )
        )
        SELECT 
            d1.user_id,
            COUNT(*) as total_reviews,
            AVG(d1.rating) as avg_rating,
            SUM(d1.helpful_vote) as total_helpful_votes,
            COALESCE(ubp.buy_count, 0) as total_buy_products,
            utc.category as top_category,
            MIN(d1.timestamp) as first_review_date,
            MAX(d1.timestamp) as last_review_date
        FROM merge_data d1
        LEFT JOIN user_buy_products ubp ON d1.user_id = ubp.user_id
        LEFT JOIN user_top_category utc ON d1.user_id = utc.user_id AND utc.rn = 1
        GROUP BY d1.user_id, ubp.buy_count, utc.category
    """
    dim_users_df = spark.sql(dim_users_query)
    dim_users_df.write.format("jdbc").option("url", postgres_url).option(
        "dbtable", f"{WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.dim_users"
    ).option("user", f"{WAREHOUSE_USER}").option(
        "password", f"{WAREHOUSE_PASSWORD}"
    ).option(
        "driver", "org.postgresql.Driver"
    ).mode(
        "append"
    ).save()
    print("[INFO] Create dim_users table successfully!!!")

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
        WITH sell_products AS (
            SELECT parent_product_id, COUNT(*) as sell_count
            FROM merge_data
            WHERE verified_purchase = true
            GROUP BY parent_product_id
        )
        SELECT 
            d1.parent_product_id,
            COUNT(*) as total_reviews,
            ROUND(AVG(d1.rating)) as avg_rating,
            SUM(d1.helpful_vote) as total_helpful_votes,
            COALESCE(sp.sell_count, 0) as total_sell_products
        FROM merge_data d1
        LEFT JOIN sell_products sp ON d1.parent_product_id = sp.parent_product_id
        GROUP BY d1.parent_product_id, sp.sell_count
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

    ## dim_categories
    dim_categories_query = """
        WITH verified_purchases AS (
            SELECT category, COUNT(*) as verified_count
            FROM merge_data
            WHERE verified_purchase = true
            GROUP BY category
        )
        SELECT 
            d1.category,
            COUNT(DISTINCT d1.parent_product_id) as total_products,
            SUM(d1.helpful_vote) as total_helpful_votes,
            COUNT(*) as total_reviews,
            ROUND(AVG(d1.rating)) as avg_rating,
            COALESCE(vp.verified_count, 0) as verified_purchases
        FROM merge_data d1
        LEFT JOIN verified_purchases vp ON d1.category = vp.category
        GROUP BY d1.category, vp.verified_count
    """
    dim_categories_df = spark.sql(dim_categories_query)
    dim_categories_df.write.format("jdbc").option("url", postgres_url).option(
        "dbtable", f"{WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.dim_categories"
    ).option("user", f"{WAREHOUSE_USER}").option(
        "password", f"{WAREHOUSE_PASSWORD}"
    ).option(
        "driver", "org.postgresql.Driver"
    ).mode(
        "append"
    ).save()
    print("[INFO] Create dim_categories table successfully!!!")

    ## dim_store_performance
    dim_store_performance_query = """
        WITH store_revenue AS (
            SELECT store, SUM(price) as revenue_sum
            FROM merge_data
            WHERE price IS NOT NULL AND store IS NOT NULL
            GROUP BY store
        )
        SELECT 
            d1.store,
            COUNT(*) as total_reviews,
            ROUND(AVG(d1.rating)) as avg_rating,
            COUNT(DISTINCT d1.parent_product_id) as total_sell_products,
            COALESCE(sr.revenue_sum, 0) as total_revenue
        FROM merge_data d1
        LEFT JOIN store_revenue sr ON d1.store = sr.store
        WHERE d1.store IS NOT NULL
        GROUP BY d1.store, sr.revenue_sum
        HAVING d1.store IS NOT NULL
    """
    dim_store_performance_df = spark.sql(dim_store_performance_query)
    dim_store_performance_df.write.format("jdbc").option("url", postgres_url).option(
        "dbtable", f"{WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.dim_store_performance"
    ).option("user", f"{WAREHOUSE_USER}").option(
        "password", f"{WAREHOUSE_PASSWORD}"
    ).option(
        "driver", "org.postgresql.Driver"
    ).mode(
        "append"
    ).save()
    print("[INFO] Create dim_store_performance table successfully!!!")

    ## fact_products
    fact_products_query = """
        SELECT 
            parent_product_id,
            FIRST(category) as category,
            FIRST(store) as store,
            FIRST(product_title) as product_title,
            FIRST(price) as price,
            FIRST(brand) as brand,
            FIRST(material) as material
        FROM merge_data
        GROUP BY parent_product_id
    """
    fact_products_df = spark.sql(fact_products_query)
    fact_products_df.write.format("jdbc").option("url", postgres_url).option(
        "dbtable", f"{WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.fact_products"
    ).option("user", f"{WAREHOUSE_USER}").option(
        "password", f"{WAREHOUSE_PASSWORD}"
    ).option(
        "driver", "org.postgresql.Driver"
    ).mode(
        "append"
    ).save()
    print("[INFO] Create fact_products table successfully!!!")

    ## fact_reviews
    fact_reviews_query = """
        SELECT 
            review_id, 
            parent_product_id, 
            user_id, 
            time_id, 
            product_id, 
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
