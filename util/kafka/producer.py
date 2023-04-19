from kafka import KafkaProducer
import os
import json
from dotenv import load_dotenv
load_dotenv()


class KafkaProducerSingleton:
    __instance = None
    __bootstrap_servers = [os.getenv("KAFKA_ENDPOINT")]

    @staticmethod
    def getInstance(bootstrap_servers=__bootstrap_servers):
        """ Static access method. """
        if KafkaProducerSingleton.__instance is None:
            KafkaProducerSingleton(bootstrap_servers)
        return KafkaProducerSingleton.__instance

    def __init__(self, bootstrap_servers=__bootstrap_servers):
        """ Virtually private constructor. """
        if KafkaProducerSingleton.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            self.producer = KafkaProducer(
                bootstrap_servers=[os.getenv("KAFKA_ENDPOINT")],
                sasl_mechanism='SCRAM-SHA-256',
                security_protocol='SASL_SSL',
                sasl_plain_username=os.getenv("KAFKA_USERNAME"),
                sasl_plain_password=os.getenv("KAFKA_PASSWORD"),
                value_serializer=lambda m: json.dumps(m).encode('ascii')
            )
            KafkaProducerSingleton.__instance = self


KafkaProducerSingleton()
