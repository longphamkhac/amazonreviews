import glob
import os

from minio import Minio

from config import *

# from config_k8s import *


def upload_s3(local_folders, s3_folder):
    minio_client = Minio(
        endpoint=ENDPOINT, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False
    )

    bucket_name = "amazonreviews"
    isFound = minio_client.bucket_exists(bucket_name=BUCKET_NAME)
    if not isFound:
        minio_client.make_bucket(bucket_name=bucket_name)

    for data_type in os.listdir(local_folders):
        for file in glob.glob(
            f"{local_folders}/{data_type}/*"
        ):  # data_type: [user_reviews, item_metadata]
            filename = file.split("/")[-1]
            object_name = f"{s3_folder}/{data_type}/{filename}"
            minio_client.fput_object(
                bucket_name=BUCKET_NAME, object_name=object_name, file_path=file
            )
    print("[INFO] Upload raw data successfully !!!")


if __name__ == "__main__":
    local_folders = "data"
    s3_folder = RAW_DATA_FOLDER
    upload_s3(local_folders, s3_folder)
