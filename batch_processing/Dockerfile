# FROM apache/spark-py:v3.4.0
FROM longpk1/spark_processing:latest

# USER root

# RUN apt-get update && \
#     apt-get -y install sudo netcat && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# WORKDIR /opt/spark/work-dir

# COPY requirements.txt .
# RUN pip install -r requirements.txt

COPY upload_s3.py .
COPY convert_raw2delta_avro.py .
COPY convert_merge2delta.py .
COPY read_streaming_data.py .
COPY adding_uuidv7.py .
COPY generate_gold_schema.py .
COPY create_tables.py .
COPY postgresql_client.py .
COPY config_k8s.py .
COPY utils.py .

WORKDIR /opt/spark/jars

# RUN rm -f hadoop-aws-*.jar aws-java-sdk-bundle-*.jar
# COPY jars/hadoop-aws-3.3.4.jar .
# COPY jars/aws-java-sdk-bundle-1.12.262.jar .
# COPY jars/delta-core_2.12-2.4.0.jar .
# COPY jars/delta-storage-2.3.0.jar .
# COPY jars/spark-avro_2.12-3.4.3.jar .
# COPY jars/spark-sql-kafka-0-10_2.12-3.4.3.jar .
# COPY jars/kafka-clients-3.4.0.jar .
# COPY jars/commons-pool2-2.12.1.jar .
# COPY jars/spark-streaming-kafka-0-10_2.13-3.4.3.jar .
# COPY jars/spark-token-provider-kafka-0-10_2.12-3.4.3.jar .
# COPY jars/spark-core_2.13-3.4.3.jar .
# COPY jars/postgresql-42.7.5.jar .

USER ${spark_uid}