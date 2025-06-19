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
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.fact_products CASCADE",
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.dim_time CASCADE",
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.dim_users CASCADE",
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.dim_reviews CASCADE",
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{WAREHOUSE_SCHEMA}.dim_products CASCADE",
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

    # Dimension: dim_users
    dim_users_table = f"{WAREHOUSE_SCHEMA}.dim_users"
    dim_users_create = f"""
        CREATE TABLE IF NOT EXISTS {dim_users_table} (
            user_id VARCHAR PRIMARY KEY,
            total_reviews BIGINT,
            avg_rating FLOAT,
            total_helpful_votes BIGINT,
            total_buy_products BIGINT,
            top_category VARCHAR,
            first_review_date TIMESTAMP,
            last_review_date TIMESTAMP
        );
    """
    pc.execute_query(dim_users_create)

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
            parent_product_id VARCHAR PRIMARY KEY,
            total_reviews BIGINT,
            avg_rating FLOAT,
            total_helpful_votes BIGINT,
            total_sell_products BIGINT
        );
    """
    pc.execute_query(dim_products_create)

    # Dimension: dim_categories
    dim_categories_table = f"{WAREHOUSE_SCHEMA}.dim_categories"
    dim_categories_create = f"""
        CREATE TABLE IF NOT EXISTS {dim_categories_table} (
            category VARCHAR PRIMARY KEY,
            total_products BIGINT,
            total_helpful_votes BIGINT,
            total_reviews BIGINT,
            avg_rating FLOAT,
            verified_purchases BIGINT
        );
    """
    pc.execute_query(dim_categories_create)

    # Dimension: dim_store_performance
    dim_store_performance_table = f"{WAREHOUSE_SCHEMA}.dim_store_performance"
    dim_store_performance_create = f"""
        CREATE TABLE IF NOT EXISTS {dim_store_performance_table} (
            store VARCHAR PRIMARY KEY,
            total_reviews BIGINT,
            avg_rating FLOAT,
            total_sell_products BIGINT,
            total_revenue FLOAT
        );
    """
    pc.execute_query(dim_store_performance_create)

    # Dimension: fact_products
    fact_products_table = f"{WAREHOUSE_SCHEMA}.fact_products"
    fact_products_create = f"""
        CREATE TABLE IF NOT EXISTS {fact_products_table} (
            parent_product_id VARCHAR,
            category VARCHAR,
            store VARCHAR,
            product_title VARCHAR,
            price FLOAT,
            brand VARCHAR,
            material VARCHAR,
            PRIMARY KEY (parent_product_id),
            FOREIGN KEY (parent_product_id) REFERENCES {WAREHOUSE_SCHEMA}.dim_products(parent_product_id),
            FOREIGN KEY (category) REFERENCES {WAREHOUSE_SCHEMA}.dim_categories(category),
            FOREIGN KEY (store) REFERENCES {WAREHOUSE_SCHEMA}.dim_store_performance(store)
        );
    """
    pc.execute_query(fact_products_create)

    # Dimension: fact_reviews
    fact_reviews_table = f"{WAREHOUSE_SCHEMA}.fact_reviews"
    fact_reviews_create = f"""
        CREATE TABLE IF NOT EXISTS {fact_reviews_table} (
            review_id VARCHAR,
            parent_product_id VARCHAR,
            user_id VARCHAR,
            time_id VARCHAR,
            product_id VARCHAR,
            rating FLOAT,
            verified_purchase BOOLEAN,
            helpful_vote BIGINT,
            PRIMARY KEY (review_id),
            FOREIGN KEY (review_id) REFERENCES {WAREHOUSE_SCHEMA}.dim_reviews(review_id),
            FOREIGN KEY (parent_product_id) REFERENCES {WAREHOUSE_SCHEMA}.fact_products(parent_product_id),
            FOREIGN KEY (user_id) REFERENCES {WAREHOUSE_SCHEMA}.dim_users(user_id),
            FOREIGN KEY (time_id) REFERENCES {WAREHOUSE_SCHEMA}.dim_time(time_id)
        );
    """
    pc.execute_query(fact_reviews_create)

    print("[INFO] Create SQL tables for gold schema successfully!!!")


if __name__ == "__main__":
    create_tables()
