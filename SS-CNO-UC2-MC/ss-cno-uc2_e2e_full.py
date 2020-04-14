import json
from kafka import KafkaConsumer, KafkaProducer
from settings import KAFKA_SERVER, KAFKA_API_VERSION,\
                     KAFKA_OCNO_TOPIC

from write_kafka import start_kafka_producer, write_decision_to_kafka,\
                ss_cno_uc2_ocno, ss_cno_uc2_edge_selector, ocno_ss_cno_uc2
import sys


KAFKA_CLIENT_ID = 'SS-CNO-UC2'

def ss_cno_uc2_algorithm(function, mode, nfvi_uuid_list):
    """ Based on information from a msg from edge selector, CNO algorithm decides
    GPU, CPU and nfvi_id to be used. This required information will be sent to
    O-CNO if there is no reserved resources available.
    Args:
        funtion: 'vspeech', 'vspeech_vdetection', 'vdetection', or 'none'
        mode: 'safe-remote', 'live-remote', or 'safe-local'
        nfvi_uuid_list: [] or ['tid', 'ncsrd']
    Returns:
        dict: {'GPU': [vspeech, vdetection], 'CPU': 0, 'nfvi_id': 'ncsrd'}
    """
    dict_return = {'GPU': [], 'CPU': [], 'nfvi_id': 'ncsrd'}

    if function == 'vdetection': # if vdetection then always use GPU if ncsrd is available
        dict_return['GPU'] = ['vdetection']

        if nfvi_uuid_list == [] or 'ncsrd' in nfvi_uuid_list:
            dict_return['nfvi_id'] = 'ncsrd'
        else: # ncsrd is not available, then have to use CPU in one of nfvi location
            dict_return['GPU'] = []
            dict_return['CPU'] = ['vdetection']            
            dict_return['nfvi_id'] = nfvi_uuid_list[0]

    elif function == 'vspeech_vdetection': # always use GPU if ncsrd is available
        dict_return['GPU'] = ['vspeech', 'vdetection']
        
        if nfvi_uuid_list == [] or 'ncsrd' in nfvi_uuid_list:
            dict_return['nfvi_id'] = 'ncsrd'
        else: # ncsrd is not available, then have to use CPU in one of nfvi location
            dict_return['GPU'] = []
            dict_return['CPU'] = ['vspeech', 'vdetection']            
            dict_return['nfvi_id'] = nfvi_uuid_list[0]
    elif function == 'vspeech': # use GPU in live case, otherwise use CPU
        if 'live' in mode:
            dict_return['GPU'] = ['vspeech']

            if nfvi_uuid_list == [] or 'ncsrd' in nfvi_uuid_list:
                dict_return['nfvi_id'] = 'ncsrd'
            else: # ncsrd is not available, then have to use CPU in one of nfvi location
                dict_return['GPU'] = []
                dict_return['CPU'] = ['vspeech']
                dict_return['nfvi_id'] = nfvi_uuid_list[0]
        else: # if recorded case, use CPU
            dict_return['GPU'] = []
            dict_return['CPU'] = ['vspeech']
            if nfvi_uuid_list == []:
                dict_return['nfvi_id'] = 'tid'
            else:
                dict_return['nfvi_id'] = nfvi_uuid_list[0]
    else: # when function == none
        dict_return['GPU'] = []
        dict_return['CPU'] = []
        if nfvi_uuid_list == []:
            dict_return['nfvi_id'] = 'tid'
        else:
            dict_return['nfvi_id'] = nfvi_uuid_list[0]
    return dict_return

def ss_cno_uc2():  

    # See more: https://kafka-python.readthedocs.io/en/master/apidoc/KafkaConsumer.html
    consumer = KafkaConsumer(bootstrap_servers=KAFKA_SERVER, \
                    client_id=KAFKA_CLIENT_ID, \
                    enable_auto_commit=True, \
                    value_deserializer=lambda v: json.loads(v.decode('utf-8', 'ignore')),
                    api_version=KAFKA_API_VERSION)
    
    kafka_topic = KAFKA_OCNO_TOPIC

    consumer.subscribe(pattern = kafka_topic)
    print("SS-CNO (UC2) is subscribing to {} kafka topic...".format(kafka_topic))

    producer = start_kafka_producer()

    for msg in consumer:  
        #print('\n######### new msg from kafka #########')
        receiver = msg.value['receiver']
        if receiver != 'SS-CNO-UC2-MC':
            continue

        sender = msg.value['sender']
        
        print('\n######### new msg from kafka #########')

        if sender == 'O-CNO':
            #print('--- SS-CNO-UC2-MC: received a reply from O-CNO, sent a reply to edge-selector ---')

            GPU = msg.value['resource']['GPU']
            session_uuid = msg.value['option']
            nfvi = msg.value['nfvi']
            CPU = []
            print('O-CNO --> SS-CNO (UC2): You can use {} GPU(s) in {} edge.'.format(len(GPU), nfvi))
            # ************* for testing, will uncomment for real scenario *************
            
            if GPU != [] and CPU != []:
                print('SS-CNO (UC2) --> edge selector: recommendation resources for {} edge - GPU: {}, CPU: {}'.format(nfvi, GPU, CPU))
            elif GPU != []:
                print('SS-CNO (UC2) --> edge selector: recommendation resources for {} edge - GPU: {}'.format(nfvi, GPU))
            else:
                print('SS-CNO (UC2) --> edge selector: recommendation resources for {} edge - CPU: {}'.format(nfvi, CPU))

            ss_cno_uc2_edge_selector(producer, GPU, CPU, session_uuid, nfvi)
            

        elif sender == 'edge-selector':

            
            # receiving input from edge-selector
            function = msg.value['payload']['function']
            mode = msg.value['payload']['mode']
            session_uuid = msg.value['session_uuid']
            nfvi_uuid_list = msg.value['payload']['nfvi_uuid_list']

            ####### run magic SS-CNO algorithm to make decision ######
            if nfvi_uuid_list == '':
                nfvi_uuid_list = []
            dict_return = ss_cno_uc2_algorithm(function, mode, nfvi_uuid_list)
            #num_GPU = len(dict_return['GPU'])
            GPU = dict_return['GPU']
            CPU = dict_return['CPU']
            nfvi_id = dict_return['nfvi_id']
            '''
            nfvi_id = ''

            if nfvi_uuid_list == '':
                nfvi_uuid_list = []

            if num_GPU > 0:
                if nfvi_uuid_list == []:
                    nfvi_id = 'ncsrd'
                elif 'ncsrd' in nfvi_uuid_list:
                    nfvi_id = 'ncsrd'
                #elif 'ote' in nfvi_uuid_list:
                #    nfvi_id = 'ote'
            elif nfvi_uuid_list: 
                nfvi_id = nfvi_uuid_list[0]
            '''

            ##### comment those lines below when testing with IBM only
            
            if GPU != []: # send msg to O-CNO if asking to use GPU, otherwise reply directly to edge selector
                print('Edge selector --> SS-CNO (UC2): {}, {}.'.format(function, mode))
                #print('--- SS-CNO-UC2-MC: received a request from edge_selector, sent a request to O-CNO ---')
                ss_cno_uc2_ocno(producer, 'SS-CNO-UC2-MC', 'O-CNO', GPU, session_uuid, nfvi_id)
                print('SS-CNO (UC2) --> O-CNO: Can I use {} GPU(s) in {} edge?'.format(len(GPU), nfvi_id))
            else:
                if GPU != [] and CPU != []:
                    print('SS-CNO (UC2) --> edge selector: recommendation resources for {} edge - GPU: {}, CPU: {}'.format(nfvi_id, GPU, CPU))
                elif GPU != []:
                    print('SS-CNO (UC2) --> edge selector: recommendation resources for {} edge - GPU: {}'.format(nfvi_id, GPU))
                else:
                    print('SS-CNO (UC2) --> edge selector: recommendation resources for {} edge - CPU: {}'.format(nfvi_id, CPU))

                ss_cno_uc2_edge_selector(producer, GPU, CPU, session_uuid, nfvi_id)
            
            ### for testing only, use above line when in real scenario *************
            #print('--- SS-CNO-UC2-MC: received a request from edge_selector, reply directly to edge selector ---')
            #ss_cno_uc2_edge_selector(producer, GPU, CPU, session_uuid, nfvi_id)

if __name__ == '__main__':
    ss_cno_uc2()