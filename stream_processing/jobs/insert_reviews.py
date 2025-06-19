import json
from datetime import datetime
from time import sleep
from postgresql_client import PostgresSQLClient
import random

DATABABSE = "demo"
USER = "admin"
PASSWORD = "root"

DATA_FOLDER = "Data/processed"
TABLE_NAME = "raw_reviews"
JSON_FILE = f"{DATA_FOLDER}/Magazine_Subscriptions.jsonl"

def main():
    pc = PostgresSQLClient(
        database=DATABABSE,
        user=USER,
        password=PASSWORD,
        host="postgres-svc.infrastructure.svc.cluster.local"
    )

    create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            created VARCHAR,
            rating FLOAT,
            title VARCHAR,
            text VARCHAR,
            small_image_urls VARCHAR[],
            medium_image_urls VARCHAR[],
            large_image_urls VARCHAR[],
            asin VARCHAR,
            parent_asin VARCHAR,
            user_id VARCHAR,
            timestamp VARCHAR,
            helpful_vote BIGINT,
            verified_purchase BOOLEAN
        );
    """

    pc.execute_query(create_table_query)
    print("[INFO] Create SQL table successfully !!!")
    columns = pc.get_columns(table_name=TABLE_NAME)
    
    # Insert SQL table
    with open(JSON_FILE) as files:
        for file in files:
            json_data = json.loads(file)

            created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            record = [created]
            # if json_data["parent_asin"] != "B01FV533KW":
            #     continue
            for key, value in json_data.items():
                if key == "images":
                    small_image_urls, medium_image_urls, large_image_urls = [], [], []
                    for item in value:
                        for type, image_url in item.items():
                            if type == "small_image_url":
                                small_image_urls.append(image_url)
                            elif type == "medium_image_url":
                                medium_image_urls.append(image_url)
                            elif type == "large_image_url":
                                large_image_urls.append(image_url)
                    record.append(small_image_urls)
                    record.append(medium_image_urls)
                    record.append(large_image_urls)

                elif key == "timestamp":
                    record.append(str(value))
                else:
                    record.append(value)

            print()
            insert_table_query = f"""
                INSERT INTO {TABLE_NAME} ({",".join(columns)})
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            pc.execute_query(insert_table_query, tuple(record))
            print(record)
            time_sleep = random.randrange(1, 5, 1)
            sleep(time_sleep)

if __name__ == "__main__":
    main()
