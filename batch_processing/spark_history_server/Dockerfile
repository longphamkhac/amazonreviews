FROM apache/spark-py:v3.4.0

USER root

RUN apt-get update && \
    apt-get -y install sudo netcat && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/spark/jars

RUN rm -f hadoop-aws-*.jar aws-java-sdk-bundle-*.jar
COPY jars/hadoop-aws-3.3.4.jar .
COPY jars/aws-java-sdk-bundle-1.12.262.jar .

USER ${spark_uid}

# Start History Server by default
CMD ["/opt/spark/bin/spark-class", "org.apache.spark.deploy.history.HistoryServer"]