import json
from datetime import datetime
from time import sleep
from postgresql_client import PostgresSQLClient
import random

DATABABSE = "demo"
USER = "admin"
PASSWORD = "root"

DATA_FOLDER = "Data/processed"
TABLE_NAME = "raw_item_metadata"
JSON_FILE = f"{DATA_FOLDER}/meta_Magazine_Subscriptions.jsonl"

def main():
    pc = PostgresSQLClient(
        database=DATABABSE,
        user=USER,
        password=PASSWORD,
        host="postgres-svc.infrastructure.svc.cluster.local"
    )

    # Create SQL table 
    create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            created VARCHAR,
            main_category VARCHAR,
            title VARCHAR,
            price FLOAT,
            hi_res_images VARCHAR[],
            large_images VARCHAR[],
            thumb_images VARCHAR[],
            store VARCHAR,
            brand VARCHAR,
            material VARCHAR,
            style VARCHAR,
            color VARCHAR,
            parent_asin VARCHAR
        )
    """

    pc.execute_query(create_table_query)
    print("[INFO] Create SQL table successfully !!!")
    columns = pc.get_columns(table_name=TABLE_NAME)

    # Insert SQL table
    with open(JSON_FILE) as files:
        for file in files:
            raw_data = json.loads(file)

            created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            data = [created]
            # if raw_data["parent_asin"] != "B01FV533KW":
            #     continue
            for key, value in raw_data.items():
                if key in ["features", "videos", "categories", "bought_together", "average_rating", "rating_number", "description"]:
                    continue
                elif key == "images":
                    hi_res_images, large_images, thumb_images = [], [], []
                    for item in value:
                        for type, urls in item.items():
                            if isinstance(urls, list):
                                pass
                            else:
                                if type == "hi_res":
                                    hi_res_images.append(urls)
                                elif type == "large":
                                    large_images.append(urls)
                                elif type == "thumb":
                                    thumb_images.append(urls)

                    data.append(hi_res_images)
                    data.append(large_images)
                    data.append(thumb_images)
                elif key == "details":
                    data.append(value.get("Brand", None))
                    data.append(value.get("Material", None))
                    data.append(value.get("Style", None))
                    data.append(value.get("Color", None))
                else:
                    data.append(value)

            print()
            insert_table_query = f"""
                INSERT INTO {TABLE_NAME} ({",".join(columns)})
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            pc.execute_query(insert_table_query, tuple(data))
            print(data)
            time_sleep = random.randrange(1, 5, 1)
            sleep(time_sleep)

if __name__ == "__main__":
    main()
