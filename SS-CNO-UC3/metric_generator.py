


import json
from kafka import KafkaConsumer, KafkaProducer
from settings import KAFKA_SERVER, KAFKA_CLIENT_ID, KAFKA_API_VERSION, KAFKA_MONITORING_TOPICS, \
    KAFKA_TRANSLATION_TOPIC_SUFFIX
import csv
from pathlib import Path

def write_template_msg():
    consumer = KafkaConsumer(bootstrap_servers=KAFKA_SERVER, client_id=KAFKA_CLIENT_ID, enable_auto_commit=True,
                             value_deserializer=lambda v: json.loads(v.decode('utf-8', 'ignore')),
                             api_version=KAFKA_API_VERSION, )

    file_metric_template = 'metric_template.py'
    topic_uc3 = KAFKA_MONITORING_TOPICS["uc3_translation"]
    consumer.subscribe(pattern = topic_uc3)
    print("after subscribing...", topic_uc3)
    for msg in consumer:
        #if msg.value['mano']['vdu']['name'] == 'vCDN-2-vCache-edge-vdu-1':
        if 'vCache-edge-vdu' in msg.value['mano']['vdu']['name']:
            f = open(file_metric_template, "w")  
            msg.value['analysis'] = {"action": True}
            msg.value['execution'] = {"planning": "vnf_scale_out", "value": None}
            f.write('METRIC_TEMPLATE = ' + str(msg.value))
            f.close()
            break

# metric_value should be 'do_nothing', 'vnf_scale_out' or 'vnf_scale_in'
def generate_metric(metric_value):
    write_template_msg()
    from metric_template import METRIC_TEMPLATE
    metric = METRIC_TEMPLATE
    if metric_value == 'do_nothing':
        metric['analysis']['action'] = False
    elif metric_value == 'vnf_scale_out':     	
        metric['analysis']['action'] = True
    elif metric_value == 'vnf_scale_in':
        metric['execution']['planning'] = 'vnf_scale_in'
    else:
    	return None
    return metric
'''
def generate_metric_scale_in(action):
    write_template_msg()
    from metric_template import METRIC_TEMPLATE

    metric = METRIC_TEMPLATE
    metric['execution']['planning'] = action
    return metric
'''