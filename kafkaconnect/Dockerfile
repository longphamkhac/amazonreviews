FROM confluentinc/cp-kafka-connect:7.0.9 as cp
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-s3:10.5.21

FROM quay.io/strimzi/kafka:0.46.0-kafka-4.0.0

USER root:root
RUN mkdir -p /opt/kafka/plugins/debezium-postgres-connector/ /opt/kafka/plugins/kafka-connect-s3/
RUN curl -L https://repo1.maven.org/maven2/io/debezium/debezium-connector-postgres/2.5.0.Final/debezium-connector-postgres-2.5.0.Final-plugin.tar.gz -o /tmp/debezium-connector-postgres.tar.gz && \
    tar -xzf /tmp/debezium-connector-postgres.tar.gz -C /opt/kafka/plugins/debezium-postgres-connector --strip-components=1 && \
    rm /tmp/debezium-connector-postgres.tar.gz

COPY --from=cp /usr/share/confluent-hub-components/confluentinc-kafka-connect-s3/ /opt/kafka/plugins/kafka-connect-s3/

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf awscliv2.zip aws

# Create a directory for AWS CLI configuration (owned by user 1001)
RUN mkdir -p /home/user/.aws && \
    chown -R 1001:1001 /home/user/.aws

USER 1001