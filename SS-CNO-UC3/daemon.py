import json
import random
from kafka import KafkaProducer
from settings import KAFKA_SERVER, KAFKA_API_VERSION, KAFKA_EXECUTION_TOPIC
from metric_generator import generate_metric
from datetime import datetime

def start_kafka_producer():
    producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER, api_version=KAFKA_API_VERSION,
                                     value_serializer=lambda v: json.dumps(v).encode('utf-8'))
    return producer
# value should be 'do_nothing', 'vnf_scale_out' or 'vnf_scale_in'
def write_decision_to_kafka(producer, value):
    # Generate a standard structure for each metric
    try:
        #now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        scaling_metric = generate_metric(value) # value is "scaling" or "no_scaling"
        #print(scaling_metric["analysis"])        
        print(scaling_metric)
        t = producer.send(KAFKA_EXECUTION_TOPIC, scaling_metric)
        result = t.get(timeout=60)
    except Exception as ex:
        print(ex)

'''
def scale_in(producer, value):
    # Generate a standard structure for each metric
    try:
        #now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        scaling_metric = generate_metric_scale_in(value) # value is "scaling" or "no_scaling"
        print(scaling_metric["execution"])
        print(scaling_metric)
        t = producer.send(KAFKA_EXECUTION_TOPIC, scaling_metric)
        result = t.get(timeout=60)
    except Exception as ex:
        print(ex)
'''