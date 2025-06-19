import json
from datetime import datetime

from config_k8s import *
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import (AvroDeserializer,
                                                  AvroSerializer)
from confluent_kafka.serialization import MessageField, SerializationContext
from postgresql_client import PostgresSQLClient
from pyflink.common import Types
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream import (CheckpointingMode, CheckpointStorage,
                                StreamExecutionEnvironment)
from pyflink.datastream.checkpoint_config import ExternalizedCheckpointCleanup
from pyflink.datastream.connectors.kafka import (FlinkKafkaConsumer,
                                                 FlinkKafkaProducer)
from pyflink.datastream.functions import (CoProcessFunction,
                                          KeyedProcessFunction, RuntimeContext)
from pyflink.datastream.state import ListStateDescriptor, ValueStateDescriptor
from pyflink.datastream.state_backend import RocksDBStateBackend
from utils import *


class AvroSerializerWrapper:
    def __init__(self, schema_registry_conf, topic):
        self.schema_registry_conf = schema_registry_conf
        self.topic = topic
        self.subject_name = f"{topic}-value"
        self.schema_registry_client, self._serializer, self.schema_str, self.ctx = (
            None,
            None,
            None,
            None,
        )

    def get_schema(self):
        assert self.schema_registry_client
        subjects = self.schema_registry_client.get_subjects()
        assert self.subject_name in subjects
        self.schema_str = self.schema_registry_client.get_latest_version(
            self.subject_name
        ).schema.schema_str

    def get_serializer(self):
        if self._serializer is None:
            self.ctx = SerializationContext(self.topic, MessageField.VALUE)
            self.schema_registry_client = SchemaRegistryClient(
                self.schema_registry_conf
            )
            self.get_schema()
            self._serializer = AvroSerializer(
                self.schema_registry_client, self.schema_str
            )
        return self._serializer

    def serialize(self, record):
        try:
            return self.get_serializer()(record, self.ctx)
        except:
            print("[INFO] Invalid record !!!")
            return None


serializer_wrapper = AvroSerializerWrapper(
    schema_registry_conf=SCHEMA_REGISTRY_CONF, topic=MERGE_TOPIC
)


class AvroDeserializerWrapper:
    def __init__(self, schema_registry_conf, topic):
        self.schema_registry_conf = schema_registry_conf
        self.topic = topic
        self.subject_name = f"{topic}-value"
        self.schema_registry_client, self._deserializer, self.schema_str, self.ctx = (
            None,
            None,
            None,
            None,
        )

    def get_schema(self):
        assert self.schema_registry_client
        subjects = self.schema_registry_client.get_subjects()
        assert self.subject_name in subjects
        self.schema_str = self.schema_registry_client.get_latest_version(
            self.subject_name
        ).schema.schema_str

    def get_deserializer(self):
        if self._deserializer is None:
            self.ctx = SerializationContext(self.topic, MessageField.VALUE)
            self.schema_registry_client = SchemaRegistryClient(
                self.schema_registry_conf
            )
            self.get_schema()
            self._deserializer = AvroDeserializer(
                self.schema_registry_client, self.schema_str
            )
        return self._deserializer

    def deserialize(self, record):
        try:
            return self.get_deserializer()(record, self.ctx)
        except:
            print("[INFO] Invalid record !!!")
            return None


deserializer_wrapper = AvroDeserializerWrapper(
    schema_registry_conf=SCHEMA_REGISTRY_CONF, topic=MERGE_TOPIC
)


def serialize(record):
    avro_bytes = serializer_wrapper.serialize(record)  # bytes
    if avro_bytes is None:
        return None
    converted_str = avro_bytes.decode("latin1")  # string
    return converted_str


def deserialize(record_str):
    avro_bytes = record_str.encode("latin1")  # bytes
    print("=============================================")
    print(type(avro_bytes))
    print(avro_bytes)
    record_dict = deserializer_wrapper.deserialize(avro_bytes)  # dict
    print(f"{record_dict}")
    print("=============================================\n")
    return record_dict


def create_table(table_name):
    pc = PostgresSQLClient(
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOSTNAME,
    )

    create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            created VARCHAR,
            rating INT,
            review_title VARCHAR,
            review_text VARCHAR,
            product_id VARCHAR,
            parent_product_id VARCHAR,
            user_id VARCHAR,
            timestamp VARCHAR,
            helpful_vote INT,
            verified_purchase BOOLEAN,
            category VARCHAR,
            product_title VARCHAR,
            price FLOAT,
            store VARCHAR,
            brand VARCHAR,
            material VARCHAR,
            style VARCHAR,
            color VARCHAR
        )
    """

    pc.execute_query(create_table_query)
    print("[INFO] Create SQL table successfully !!!")


def process_features(record):
    processed_record = {}

    for key, value in record.items():
        if key == "timestamp":
            dt_object = datetime.fromtimestamp(int(value) // 1000.0)
            processed_record[key] = dt_object.strftime("%Y-%m-%d %H:%M:%S")
        else:
            processed_record[key] = value

    processed_record_str = serialize(processed_record)
    return processed_record_str


class Printer(KeyedProcessFunction):
    def process_element(self, value, ctx: KeyedProcessFunction.Context):
        key = ctx.get_current_key()
        print(f"[INFO] Key: {key}, Value: {value}\n")
        return value


class MergeReviewsWithMetadata(CoProcessFunction):
    def open(self, ctx: RuntimeContext):
        self.metadata_state = ctx.get_state(
            ValueStateDescriptor("metadata", Types.STRING())
        )
        self.reviews_state = ctx.get_list_state(
            ListStateDescriptor("reviews", Types.STRING())
        )

        self.review_schema = json.loads(get_schema(REVIEW_SUBJECT_NAME))
        self.metadata_schema = json.loads(get_schema(METADATA_SUBJECT_NAME))

    def process_element1(self, value, ctx: CoProcessFunction.Context):
        merged_record = {}
        review = json.loads(value)["after"]
        metadata = (
            json.loads(self.metadata_state.value())["after"]
            if self.metadata_state.value()
            else None
        )

        if metadata:
            print("[INFO] Merging in Review Stream !!!")
            for field in self.review_schema["fields"]:
                for key in field.keys():
                    if key != "name":
                        continue
                    name = field[key]
                    if name == "product_id":
                        merged_record[name] = review["asin"]
                    elif name == "review_title":
                        merged_record[name] = review["title"]
                    elif name == "review_text":
                        merged_record[name] = review["text"]
                    elif name == "parent_product_id":
                        merged_record[name] = review["parent_asin"]
                    else:
                        merged_record[name] = review[name]

            for field in self.metadata_schema["fields"]:
                for key in field.keys():
                    if key != "name":
                        continue
                    name = field[key]
                    if name == "parent_product_id":
                        continue
                    elif name == "product_title":
                        merged_record[name] = metadata["title"]
                    elif name == "category":
                        merged_record[name] = metadata["main_category"]
                    else:
                        merged_record[name] = metadata[name]
            yield merged_record
        else:
            # print("[INFO] Adding value to Review state !!!")
            self.reviews_state.add(value)

    def process_element2(self, value, ctx: CoProcessFunction.Context):
        self.metadata_state.update(value)

        merged_record = {}
        metadata = json.loads(value)["after"]
        reviews = list(self.reviews_state.get())

        if reviews:
            for review in reviews:
                print("[INFO] Merging in Metadata Stream !!!")
                review = json.loads(review)["after"]
                for field in self.review_schema["fields"]:
                    for key in field.keys():
                        if key != "name":
                            continue
                        name = field[key]
                        if name == "product_id":
                            merged_record[name] = review["asin"]
                        elif name == "review_title":
                            merged_record[name] = review["title"]
                        elif name == "review_text":
                            merged_record[name] = review["text"]
                        elif name == "parent_product_id":
                            merged_record[name] = review["parent_asin"]
                        else:
                            merged_record[name] = review[name]

                for field in self.metadata_schema["fields"]:
                    for key in field.keys():
                        if key != "name":
                            continue
                        name = field[key]
                        if name == "parent_product_id":
                            continue
                        elif name == "product_title":
                            merged_record[name] = metadata["title"]
                        elif name == "category":
                            merged_record[name] = metadata["main_category"]
                        else:
                            merged_record[name] = metadata[name]
                yield merged_record
            self.reviews_state.clear()


def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.add_jars(
        f"file://{JARS_PATH}/flink-java-1.20.0.jar",
        f"file://{JARS_PATH}/flink-table-api-java-bridge-1.20.0.jar",
        f"file://{JARS_PATH}/flink-streaming-java-1.20.0.jar",
        f"file://{JARS_PATH}/flink-connector-kafka-3.4.0-1.20.jar",
        f"file://{JARS_PATH}/kafka-clients-3.4.0.jar",
    )

    consumer_reviews = FlinkKafkaConsumer(
        topics="test.public.raw_reviews",
        deserialization_schema=SimpleStringSchema(),
        properties=CONSUMER_PROPS,
    )

    consumer_metadata = FlinkKafkaConsumer(
        topics="test.public.raw_item_metadata",
        deserialization_schema=SimpleStringSchema(),
        properties=CONSUMER_PROPS,
    )

    reviews_stream = env.add_source(consumer_reviews)
    metadata_stream = env.add_source(consumer_metadata)

    reviews_stream_keyed = reviews_stream.key_by(
        key_selector=lambda x: json.loads(x)["after"]["parent_asin"],
        key_type=Types.STRING(),
    )

    metadata_stream_keyed = metadata_stream.key_by(
        key_selector=lambda x: json.loads(x)["after"]["parent_asin"],
        key_type=Types.STRING(),
    )

    connected_stream = reviews_stream_keyed.connect(metadata_stream_keyed)
    enriched_stream = connected_stream.process(
        MergeReviewsWithMetadata(), output_type=Types.PICKLED_BYTE_ARRAY()
    )

    producer = FlinkKafkaProducer(
        topic=MERGE_TOPIC,
        serialization_schema=SimpleStringSchema(),
        producer_config=MERGE_PRODUCER_PROPS,
    )
    enriched_stream.map(process_features, output_type=Types.STRING()).filter(
        lambda x: x is not None
    ).add_sink(producer).name("Sink merged streams")

    env.execute("Merge streams")


if __name__ == "__main__":
    register_schema(REVIEW_SUBJECT_NAME, REVIEW_SCHEMA_PATH)
    register_schema(METADATA_SUBJECT_NAME, METADATA_SCHEMA_PATH)
    register_schema(MERGE_SUBJECT_NAME, MERGE_SCHEMA_PATH)

    create_table("merge_metadata_reviews")
    main()
