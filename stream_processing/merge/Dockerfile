FROM apache/flink:1.20.0-scala_2.12-java11

RUN apt-get update && \
    apt-get -y install sudo

RUN apt-get update -y && \
    apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev libffi-dev liblzma-dev wget && \
    wget https://www.python.org/ftp/python/3.8.0/Python-3.8.0.tgz && \
    tar -xvf Python-3.8.0.tgz && \
    cd Python-3.8.0 && \
    ./configure --without-tests --enable-shared && \
    make -j6 && \
    make install && \
    ldconfig /usr/local/lib && \
    cd .. && rm -f Python-3.8.0.tgz && rm -rf Python-3.8.0 && \
    ln -s /usr/local/bin/python3 /usr/local/bin/python && \
    wget https://bootstrap.pypa.io/pip/3.8/get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py && \
    pip3 install --upgrade pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set library path
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

WORKDIR /opt/flink/usr
COPY ./requirements.txt ./requirements.txt
RUN pip3 install -r ./requirements.txt

COPY ./config_k8s.py ./config_k8s.py
COPY ./merge_streams_avro.py ./merge_streams_avro.py
COPY ./utils.py ./utils.py
COPY ./postgresql_client.py ./postgresql_client.py
COPY ./schemas/avro ./schemas/avro

RUN apt-get update && \
    apt-get install -y netcat

RUN chmod -R 777 /opt/flink
RUN chmod +x .
COPY ./jars/flink-java-1.20.0.jar ./jars/flink-java-1.20.0.jar
COPY ./jars/flink-table-api-java-bridge-1.20.0.jar ./jars/flink-table-api-java-bridge-1.20.0.jar
COPY ./jars/flink-streaming-java-1.20.0.jar ./jars/flink-streaming-java-1.20.0.jar
COPY ./jars/flink-connector-kafka-3.4.0-1.20.jar ./jars/flink-connector-kafka-3.4.0-1.20.jar
COPY ./jars/kafka-clients-3.4.0.jar ./jars/kafka-clients-3.4.0.jar
COPY ./jars/flink-python-1.20.0.jar ./jars/flink-python-1.20.0.jar

COPY ./jars/flink-s3-fs-hadoop-1.20.0.jar ./jars/flink-s3-fs-hadoop-1.20.0.jar
COPY ./jars/hadoop-common-3.4.0.jar ./jars/hadoop-common-3.4.0.jar

RUN chown -R flink:flink /opt/flink/ &&\
    chmod -R 755 /opt/flink/
RUN mkdir /opt/flink/plugins/s3-fs-hadoop
COPY ./jars/flink-s3-fs-hadoop-1.20.0.jar /opt/flink/plugins/s3-fs-hadoop
COPY ./jars/hadoop-common-3.4.0.jar /opt/flink/plugins/s3-fs-hadoop

WORKDIR /opt/flink/usr
RUN chmod +x ./merge_streams_avro.py ./utils.py ./postgresql_client.py

ENV DISABLE_JEMALLOC=true