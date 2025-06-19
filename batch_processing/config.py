ENDPOINT = "localhost:9000"
ACCESS_KEY = "minio_access_key"
SECRET_KEY = "minio_secret_key"
BUCKET_NAME = "amazonreviews"

RAW_DATA_FOLDER = "bronze/historical-raw-data"
DELTA_DATA_FOLDER = "silver/historical-delta-format-data"
MERGE_DATA_FOLDER = "silver/historical-merge-data"
STREAMING_DATA_FOLDER = "gold/streaming-data"
REFINED_MERGE_DATA_FOLDER = "gold/merge-data"

NUM_PARTITIONS = 16

JARS_FOLDER = "jars"
HADOOP_AWS_JAR = f"{JARS_FOLDER}/hadoop-aws-3.3.4.jar"
AWS_SDK_JAR = f"{JARS_FOLDER}/aws-java-sdk-bundle-1.12.262.jar"
DELTA_CORE_JAR = f"{JARS_FOLDER}/delta-core_2.12-2.4.0.jar"
DELTA_STORAGE_JAR = f"{JARS_FOLDER}/delta-storage-2.3.0.jar"
SPARK_AVRO_JAR = f"{JARS_FOLDER}/spark-avro_2.12-3.4.3.jar"
POSTGRES_SQL_JAR = f"{JARS_FOLDER}/postgresql-42.7.5.jar"

SPARK_SQL_KAFKA_JAR = f"{JARS_FOLDER}/spark-sql-kafka-0-10_2.12-3.4.3.jar"
KAFKA_CLIENTS_JAR = f"{JARS_FOLDER}/kafka-clients-3.4.0.jar"
COMMONS_POOL_JAR = f"{JARS_FOLDER}/commons-pool2-2.12.1.jar"
SPARK_STREAMING_KAFKA_JAR = f"{JARS_FOLDER}/spark-streaming-kafka-0-10_2.13-3.4.3.jar"
SPARK_TOKEN_PROVIDER_KAFKA = f"{JARS_FOLDER}/spark-token-provider-kafka-0-10_2.12-3.4.3.jar"
SPARK_CORE_JAR = f"{JARS_FOLDER}/spark-core_2.13-3.4.3.jar"

JARS = f"{DELTA_CORE_JAR}, \
        {DELTA_STORAGE_JAR}, \
        {HADOOP_AWS_JAR}, \
        {AWS_SDK_JAR}, \
        {SPARK_AVRO_JAR}, \
        {POSTGRES_SQL_JAR}, \
        {SPARK_SQL_KAFKA_JAR}, \
        {KAFKA_CLIENTS_JAR}, \
        {COMMONS_POOL_JAR}, \
        {SPARK_STREAMING_KAFKA_JAR}, \
        {SPARK_TOKEN_PROVIDER_KAFKA}, \
        {SPARK_CORE_JAR} \
    "

SCHEMA_REGISTRY_CONF = {"url": "http://localhost:8081"}
REVIEW_SCHEMA_TOPIC = "review"
METADATA_SCHEMA_TOPIC = "metadata"
MERGE_SCHEMA_TOPIC = "merge_metadata_reviews"