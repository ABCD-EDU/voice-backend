from kafka import KafkaConsumer
import os
from dotenv import load_dotenv
load_dotenv()


class SingletonKafkaConsumer:
    def __init__(self, topic):
        self.topic = topic
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=[os.getenv("KAFKA_ENDPOINT")],
            sasl_mechanism='SCRAM-SHA-256',
            security_protocol='SASL_SSL',
            sasl_plain_username=os.getenv("KAFKA_USERNAME"),
            sasl_plain_password=os.getenv("KAFKA_PASSWORD"),
            group_id='Default',
            auto_offset_reset='earliest',
        )

    def consume(self):
        for message in self.consumer:
            yield message.value

    def change_topic(self, new_topic):
        self.consumer.unsubscribe()
        self.topic = new_topic
        self.consumer.subscribe([new_topic])
