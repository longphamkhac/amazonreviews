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
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{DATAMART_SCHEMA}.mart_parent_products CASCADE",
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{DATAMART_SCHEMA}.mart_users CASCADE",
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{DATAMART_SCHEMA}.mart_reviews CASCADE",
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{DATAMART_SCHEMA}.mart_categories CASCADE",
        f"DROP TABLE IF EXISTS {WAREHOUSE_DATABASE}.{DATAMART_SCHEMA}.mart_store_performance CASCADE",
    ]
    for query in drop_queries:
        pc.execute_query(query)

    # martension: mart_users
    mart_users_table = f"{DATAMART_SCHEMA}.mart_users"
    mart_users_create = f"""
        CREATE TABLE IF NOT EXISTS {mart_users_table} (
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
    pc.execute_query(mart_users_create)

    # martension: mart_parent_products
    mart_parent_products_table = f"{DATAMART_SCHEMA}.mart_parent_products"
    mart_parent_products_create = f"""
        CREATE TABLE IF NOT EXISTS {mart_parent_products_table} (
            parent_product_id VARCHAR PRIMARY KEY,
            total_reviews BIGINT,
            avg_rating FLOAT,
            total_helpful_votes BIGINT,
            total_sell_products BIGINT
        );
    """
    pc.execute_query(mart_parent_products_create)

    # martension: mart_categories
    mart_categories_table = f"{DATAMART_SCHEMA}.mart_categories"
    mart_categories_create = f"""
        CREATE TABLE IF NOT EXISTS {mart_categories_table} (
            category VARCHAR PRIMARY KEY,
            total_products BIGINT,
            total_helpful_votes BIGINT,
            total_reviews BIGINT,
            avg_rating FLOAT,
            verified_purchases BIGINT
        );
    """
    pc.execute_query(mart_categories_create)

    # martension: mart_store_performance
    mart_store_performance_table = f"{DATAMART_SCHEMA}.mart_store_performance"
    mart_store_performance_create = f"""
        CREATE TABLE IF NOT EXISTS {mart_store_performance_table} (
            store VARCHAR PRIMARY KEY,
            total_reviews BIGINT,
            avg_rating FLOAT,
            total_sell_products BIGINT,
            total_revenue FLOAT
        );
    """
    pc.execute_query(mart_store_performance_create)

    # martension: mart_reviews
    mart_reviews_table = f"{DATAMART_SCHEMA}.mart_reviews"
    mart_reviews_create = f"""
        CREATE TABLE IF NOT EXISTS {mart_reviews_table} (
            review_id VARCHAR,
            user_id VARCHAR,
            time_id VARCHAR,
            product_id VARCHAR,
            rating FLOAT,
            verified_purchase BOOLEAN,
            helpful_vote BIGINT,
            PRIMARY KEY (review_id)
        );
    """
    pc.execute_query(mart_reviews_create)

    print("[INFO] Create SQL tables for gold schema successfully!!!")


if __name__ == "__main__":
    create_tables()
