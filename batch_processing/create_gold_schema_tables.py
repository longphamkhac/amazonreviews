from config_k8s import *
from postgresql_client import PostgresSQLClient

pc = PostgresSQLClient(
    database=WAREHOUSE_DATABASE,
    user=WAREHOUSE_USER,
    password=WAREHOUSE_PASSWORD,
    host=WAREHOUSE_ENDPOINT,
)


def create_tables():
    # Drop dependent tables first (reverse dependency order)
    drop_queries = [
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.fact_reviews CASCADE",
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.dim_products CASCADE",
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.dim_time CASCADE",
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.dim_users CASCADE",
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.dim_reviews CASCADE",
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.dim_parent_products CASCADE",
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.dim_categories CASCADE",
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.dim_store_performance CASCADE",
    ]
    for query in drop_queries:
        pc.execute_query(query)

    # Dimension: dim_time
    dim_time_table = f"{WAREHOUSE_SCHEMA}.dim_time"
    dim_time_create = f"""
        CREATE TABLE IF NOT EXISTS {dim_time_table} (
            time_id VARCHAR PRIMARY KEY,
            review_date TIMESTAMP,
            year INTEGER,
            month INTEGER,
            day INTEGER,
            quarter INTEGER
        );
    """
    pc.execute_query(dim_time_create)

    # Dimension: dim_reviews_text
    dim_reviews_text_table = f"{WAREHOUSE_SCHEMA}.dim_reviews"
    dim_reviews_text_create = f"""
        CREATE TABLE IF NOT EXISTS {dim_reviews_text_table} (
            review_id VARCHAR PRIMARY KEY,
            review_title VARCHAR,
            review_text VARCHAR
        );
    """
    pc.execute_query(dim_reviews_text_create)

    # Dimension: dim_products
    dim_products_table = f"{WAREHOUSE_SCHEMA}.dim_products"
    dim_products_create = f"""
        CREATE TABLE IF NOT EXISTS {dim_products_table} (
            product_id VARCHAR,
            parent_product_id VARCHAR,
            store VARCHAR,
            category VARCHAR,
            product_title VARCHAR,
            price FLOAT,
            brand VARCHAR,
            material VARCHAR,
            PRIMARY KEY (product_id)
        );
    """
    pc.execute_query(dim_products_create)

    # Dimension: fact_reviews
    fact_reviews_table = f"{WAREHOUSE_SCHEMA}.fact_reviews"
    fact_reviews_create = f"""
        CREATE TABLE IF NOT EXISTS {fact_reviews_table} (
            review_id VARCHAR,
            user_id VARCHAR,
            time_id VARCHAR,
            product_id VARCHAR,
            rating FLOAT,
            verified_purchase BOOLEAN,
            helpful_vote BIGINT,
            PRIMARY KEY (review_id),
            FOREIGN KEY (review_id) REFERENCES {WAREHOUSE_SCHEMA}.dim_reviews(review_id),
            FOREIGN KEY (product_id) REFERENCES {WAREHOUSE_SCHEMA}.dim_products(product_id),
            FOREIGN KEY (time_id) REFERENCES {WAREHOUSE_SCHEMA}.dim_time(time_id)
        );
    """
    pc.execute_query(fact_reviews_create)

    print("[INFO] Create SQL tables for gold schema successfully!!!")


if __name__ == "__main__":
    create_tables()
