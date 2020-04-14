import json
from kafka import KafkaConsumer, KafkaProducer
from settings import KAFKA_SERVER, KAFKA_CLIENT_ID, KAFKA_API_VERSION,\
                     KAFKA_OCNO_TOPIC, REQUEST_TEMPLATE, EDGE_SELECTOR_REQ,\
                     EDGE_SELECTOR_RESPONSE, SS_CNO_UC2_OCNO
import sys

def start_kafka_producer():
    producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER, api_version=KAFKA_API_VERSION,
                                     value_serializer=lambda v: json.dumps(v).encode('utf-8'))
    return producer


def write_decision_to_kafka(producer, sender, receiver, num_GPU, num_CPU=0):
    metric = REQUEST_TEMPLATE
    metric['sender'] = sender
    metric['receiver'] = receiver
    metric['resource']['GPU'] = num_GPU
    metric['resource']['CPU'] = num_CPU
    try:
        t = producer.send(KAFKA_OCNO_TOPIC, metric)
        result = t.get(timeout=60)
    except Exception as ex:
        print(ex)


def ss_cno_uc2_ocno(producer, sender, receiver, GPU, session_uuid, nfvi_uuid):
    metric = SS_CNO_UC2_OCNO
    metric['sender'] = sender
    metric['receiver'] = receiver
    metric['resource']['GPU'] = GPU
    metric['option'] = session_uuid
    metric['nfvi'] = nfvi_uuid
    try:
        t = producer.send(KAFKA_OCNO_TOPIC, metric)
        result = t.get(timeout=60)
    except Exception as ex:
        print(ex)

def ocno_ss_cno_uc2(producer, sender, receiver, GPU, session_uuid, nfvi_uuid):
    metric = SS_CNO_UC2_OCNO
    metric['sender'] = sender
    metric['receiver'] = receiver
    metric['resource']['GPU'] = GPU
    metric['option'] = session_uuid
    metric['nfvi'] = nfvi_uuid
    try:
        t = producer.send(KAFKA_OCNO_TOPIC, metric)
        result = t.get(timeout=60)
    except Exception as ex:
        print(ex)

def ss_cno_uc2_edge_selector(producer, GPU, CPU, session_uuid, nfvi_uuid):
    metric = EDGE_SELECTOR_RESPONSE
    metric['resource']['GPU'] = GPU
    metric['resource']['CPU'] = CPU
    metric['resource']['nfvi_uuid'] = nfvi_uuid
    metric['session_uuid'] = session_uuid
    try:
        t = producer.send(KAFKA_OCNO_TOPIC, metric)
        result = t.get(timeout=60)
    except Exception as ex:
        print(ex)

# function_values can be out from: 'vspeech', 'vspeech_vdetection', 'vdetection', 'none'
# mode_values = ['safe-remote', 'live-remote', 'safe-local']
def edge_selector_req(producer, function, mode, nfvi_uuid_list, session_uuid):
    metric = EDGE_SELECTOR_REQ
    metric['payload']['function'] = function
    metric['payload']['mode'] = mode
    metric['payload']['nfvi_uuid_list'] = nfvi_uuid_list
    metric['session_uuid'] = session_uuid
    try:
        t = producer.send(KAFKA_OCNO_TOPIC, metric)
        result = t.get(timeout=60)
    except Exception as ex:
        print(ex)

if __name__ == '__main__':
    if len(sys.argv) == 4:        
        sender = sys.argv[1]
        receiver = sys.argv[2]
        num_GPU = int(sys.argv[3])

        producer = start_kafka_producer()
        write_decision_to_kafka(producer, sender, receiver, num_GPU)
    elif len(sys.argv) == 5: # edge_selector sends request to SS-CNO-UC2
        function = sys.argv[1]
        mode = sys.argv[2]
        nfvi_uuid_list = sys.argv[3]
        session_uuid = sys.argv[4]
        producer = start_kafka_producer()
        edge_selector_req(producer, function, mode, nfvi_uuid_list, session_uuid)
    else:
        print('Usage: python3 write_kafka sender receiver numGPU')
        print('*** or ***')
        print('Usage (edge_selector_req): python3 write_kafka function mode nfvi_uuid_list session_uuid')
        exit(1)
# nohup python3 ss-cno-uc2_e2e_full.py &> ss_cno_uc2.out &
# SS-CNO UC1: python3 write_kafka.py UC_1 O-CNO 2
# edge_selector --> SS-CNO UC2: python3 write_kafka.py vspeech_vdetection safe-local '' 123abc