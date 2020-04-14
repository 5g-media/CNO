import json
from kafka import KafkaConsumer, KafkaProducer
from settings import KAFKA_SERVER, KAFKA_CLIENT_ID, KAFKA_API_VERSION,\
                     KAFKA_OCNO_TOPIC

from write_kafka import start_kafka_producer, write_decision_to_kafka, ocno_ss_cno_uc2
import sys
'''
def get_user_id(kafka_msg):
    """ This function is used to get user id from a request message
    Args:
        kafka_msg: message listened from kafka bus
    Returns:
        String: user id
    """
    return kafka_msg.value['request']['userid']
'''
def get_receiver_id(kafka_msg):
    """ This function is used to get receiver id from a request message
    Args:
        kafka_msg: message listened from kafka bus
    Returns:
        String: receiver id
    """
    if 'receiver' not in kafka_msg.value:
        return None
    return kafka_msg.value['receiver']

def get_sender_id(kafka_msg):
    """ This function is used to get sender id from a request message
    Args:
        kafka_msg: message listened from kafka bus
    Returns:
        String: sender id
    """
    if 'sender' not in kafka_msg.value:
        return None
    return kafka_msg.value['sender']

def get_num_GPU(kafka_msg):
    """ This function is used to get number of GPU from a msg
    Args:
        kafka_msg: message listened from kafka bus
    Returns:
        String: number of GPUs
    """    
    if 'GPU' not in kafka_msg.value['resource']:
        return None
    return kafka_msg.value['resource']['GPU']


def get_num_free_GPU(list_GPU, list_free_GPU):
    """ This function is used to get a list of free GPU
    Args:
        list_GPU (list): list of GPUs to be checked
        list_free_GPU (list): list of currently free GPUs
    Returns:
        List: a subset of list_GPU containing only free GPUs
    """    
    return [g for g in list_GPU if g in list_free_GPU]    

def write_status_to_file(filename, list_GPU_id, dict_reserved_GPU, \
                            list_shared_GPU, list_free_GPU,\
                            list_occupied_GPU, list_user_id, dict_user_priority,\
                            dict_allocated_GPU_user):
    """ This function is used to set checkpoint of current resource availability
    Args:
        All current global variables status
    Returns:
        Update the file resource_availability.py
    """   
    f = open(filename, 'w')
    f.write('# =================================\n')
    f.write('# GPU management\n')
    f.write('# =================================\n')
    f.write('GPU_ID = ' + repr(list_GPU_id) + '\n')
    f.write('# UC_1: list of reserved GPUs\n')
    f.write('RESERSED_GPU = ' + repr(dict_reserved_GPU) + '\n')
    f.write('# list of GPU shared between use cases\n')
    f.write('SHARED_GPU = ' + repr(list_shared_GPU) + '\n')
    f.write('# list of GPUs currently are free\n')
    f.write('FREE_GPU = ' + repr(list_free_GPU) + '\n')
    f.write('# list of GPUs currently are occupied\n')
    f.write('OCCUPIED_GPU = ' + repr(list_occupied_GPU) + '\n')
    f.write('# ===================================\n')
    f.write('# user request priority\n')
    f.write('# higher number means higher priority\n')
    f.write('# ===================================\n')
    f.write('LIST_USER = ' + repr(list_user_id) + '\n')
    f.write('PRIORITY = ' + repr(dict_user_priority) + '\n')
    f.write('ALLOCATED_GPU_USER = ' + repr(dict_allocated_GPU_user) + '\n')
    f.close()

def reset_status_to_file(filename):
    """ This function is used to set checkpoint of current resource availability
    Args:
        filename of resource availability
    Returns:
        Update the file resource_availability.py
    """   
    f = open(filename, 'w')
    f.write('# =================================\n')
    f.write('# GPU management\n')
    f.write('# =================================\n')
    f.write('GPU_ID = [\'GPU_1\', \'GPU_2\']\n')
    f.write('# UC_1: list of reserved GPUs\n')
    f.write('RESERSED_GPU = {\'UC_1\': [\'GPU_1\'], \'UC_2\': []}\n')
    f.write('# list of GPU shared between use cases\n')
    f.write('SHARED_GPU = [\'GPU_2\']\n')
    f.write('# list of GPUs currently are free\n')
    f.write('FREE_GPU = [\'GPU_1\', \'GPU_2\']\n')
    f.write('# list of GPUs currently are occupied\n')
    f.write('OCCUPIED_GPU = []\n')
    f.write('# ===================================\n')
    f.write('# user request priority\n')
    f.write('# higher number means higher priority\n')
    f.write('# ===================================\n')
    f.write('LIST_USER = [\'UC_1\', \'UC_2\']\n')
    f.write('PRIORITY = {\'UC_1\': 1, \'UC_2\': 2}\n')
    f.write('ALLOCATED_GPU_USER = {}\n')
    f.close()

def remove_sublist(list_free_GPU, list_GPU_to_use):
    """ This function is updated the list of free GPUs
    Args:
        list_free_GPU (list): list of free GPUs
        list_GPU_to_use (list): list of GPUs to be used
    Returns:
        List: a subset of list_free_GPU after removing those being used
    """ 
    return [i for i in list_free_GPU if i not in list_GPU_to_use]


def o_cno_arbitration(list_GPU_id, dict_reserved_GPU, list_shared_GPU, list_free_GPU,\
                list_occupied_GPU, list_user_id, dict_user_priority,\
                dict_allocated_GPU_user, producer):  

    """ This is O-CNO_arbitration algorithm
    Listen to a request from SS-CNO. Based on availability of GPUs to response:
        - accept the request, only needs to use reserved GPUs of that user
        - accept the request, needs to use free GPUs from the shared pool
        - accept the request, needs to preempt other user session
        - reject the request
    Args:
        list_GPU_id (list): list of GPU ids
        dict_reserved_GPU (dict): reserved GPUs of each user
        list_shared_GPU (list): list of shared GPUs
        list_free_GPU (list): list of currently free GPUs
        list_occupied_GPU (list): list of currently occupied GPUs
        list_user_id (list): list of user ids
        dict_user_priority (dict): priority of users (higher value - higher priority)
        dict_allocated_GPU_user (dict): list of GPUs is used by each user
        producer: kafka producer to send message to
    Returns:
        No return value, loop to wait for new request and response
    """ 

    # See more: https://kafka-python.readthedocs.io/en/master/apidoc/KafkaConsumer.html
    consumer = KafkaConsumer(bootstrap_servers=KAFKA_SERVER, \
                    client_id=KAFKA_CLIENT_ID, \
                    enable_auto_commit=True, \
                    value_deserializer=lambda v: json.loads(v.decode('utf-8', 'ignore')),
                    api_version=KAFKA_API_VERSION)
    
    kafka_topic = KAFKA_OCNO_TOPIC

    consumer.subscribe(pattern = kafka_topic)
    #print("O-CNO is subscribing to {} kafka topic...".format(kafka_topic))    
    total_num_free_GPU = len(list_free_GPU)
    current_num_free_GPU = total_num_free_GPU

    # when O-CNO receives msg from UC2, this flag is set to True so that
    # O-CNO will send a response after UC1 releases the GPU
    flag_send_to_UC2 = False
    nfvi_uuid = None
    GPU = []
    session_uuid = ''
    for msg in consumer:  
        # O-CNO only consider msg with destination is 'O-CNO'
        if get_receiver_id(msg) != 'O-CNO':
            continue

        print('\n######### new msg from kafka #########')
        #print(msg.value)          

        # get user id of the request
        sender_id = get_sender_id(msg)
        if sender_id not in list_user_id:
            print('***** Error: unknown sender id *****')
            continue

        num_GPU = msg.value['resource']['GPU']
        # SS-CNO UC1 to O-CNO, GPU is the number of GPU, while SS-CNO (UC2) to
        # O-CNO, GPU is a list of functions using GPU
        #session_uuid = msg.value['option']
        

        if num_GPU is None:
            print('***** Error: wrong number of GPU ****')
            continue

        if sender_id == 'UC_1':            
            if num_GPU > total_num_free_GPU:
                print('***** Error: wrong number of occupied GPU ****')
                continue
            else:                
                current_num_free_GPU = total_num_free_GPU - num_GPU
                print('SS-CNO (UC1) --> O-CNO: UC1 is using {} GPU(s).'.\
                                format(num_GPU))
                if flag_send_to_UC2:
                    #print('--- sent a reply: UC2 can use up to {} GPU(s) ---'.\
                    #                            format(current_num_free_GPU))
                    print('O-CNO --> SS-CNO (UC2): you can use {} GPU(s) in {} edge'.format(current_num_free_GPU, nfvi_uuid))
                    #write_decision_to_kafka(producer, 'O-CNO', 'UC_2', \
                    #                            current_num_free_GPU)
                    #print('***** ', GPU, nfvi_uuid)
                    ocno_ss_cno_uc2(producer, 'O-CNO', 'SS-CNO-UC2-MC',\
                                         GPU, session_uuid, nfvi_uuid)
                    flag_send_to_UC2 = False


        elif sender_id == 'SS-CNO-UC2-MC':
            session_uuid = msg.value['option']
            GPU = msg.value['resource']['GPU']
            num_GPU = len(GPU)
            nfvi_uuid = msg.value['nfvi']
            #print('SS-CNO-UC2-MC to O-CNO: can I use {} GPU(s)?'.format(num_GPU))
            print('SS-CNO (UC2) --> O-CNO: Can I use {} GPU(s) in {} edge?'.format(num_GPU, nfvi_uuid))
            if num_GPU > total_num_free_GPU:
                print('**** There are not enough GPUs ****')

            '''
            write_decision_to_kafka(producer, 'O-CNO', 'UC_1', \
                                                max(0, total_num_free_GPU - num_GPU))

            # set the flag to True so that when O-CNO receives msg from UC1
            # notifying that UC1 has released GPU, O-CNO sends a reply to SS-CNO UC2.
            flag_send_to_UC2 = True 
            '''

            # need preemption
            if current_num_free_GPU < num_GPU: 

                if dict_user_priority['SS-CNO-UC2-MC'] <= dict_user_priority['UC_1']:
                    #write_decision_to_kafka(producer, 'O-CNO', 'UC_2', 0)
                    ocno_ss_cno_uc2(producer, 'O-CNO', 'SS-CNO-UC2-MC', [], session_uuid, nfvi_uuid)
                    print('*** reply to SS-CNO-UC2-MC: there is not available GPU ***')
                    continue

                print('O-CNO --> SS-CNO (UC1): you can use up to {} GPU(s).'.format(max(0, total_num_free_GPU - num_GPU)))
                write_decision_to_kafka(producer, 'O-CNO', 'UC_1', \
                                                max(0, total_num_free_GPU - num_GPU),\
                                                num_GPU) # num_GPU = num_CPU needed
                #print('---------- ', num_GPU)
                # set the flag to True so that when O-CNO receives msg from UC1
                # notifying that UC1 has released GPU, O-CNO sends a reply to SS-CNO UC2.
                flag_send_to_UC2 = True 
            # no need for preemption
            else:                 

                current_num_free_GPU = total_num_free_GPU - num_GPU

                # notify UC1 the maximum number of GPUs it can use
                print('O-CNO --> SS-CNO (UC1): you can use up to {} GPU(s).'.format(max(0, total_num_free_GPU - num_GPU)))
                write_decision_to_kafka(producer, 'O-CNO', 'UC_1', \
                                                max(0, total_num_free_GPU - num_GPU))


                print('--- no preemption needed, sent a reply: UC2 can use up to {} GPU(s) ---'.\
                                                format(num_GPU))
                #write_decision_to_kafka(producer, 'O-CNO', 'UC_2', num_GPU)
                ocno_ss_cno_uc2(producer, 'O-CNO', 'SS-CNO-UC2-MC', GPU, session_uuid, nfvi_uuid)
            
        
resource_status_file = 'resource_availability.py'

if __name__ == '__main__':
    if len(sys.argv) > 1:
        print('****reset resource availability****')
        reset_status_to_file(resource_status_file) 

    from resource_availability import GPU_ID, RESERSED_GPU, SHARED_GPU, FREE_GPU, \
                            OCCUPIED_GPU, LIST_USER, PRIORITY, ALLOCATED_GPU_USER

    # ============================================
    # instatiate global variables from the setting
    # ============================================
    list_GPU_id = GPU_ID
    dict_reserved_GPU = RESERSED_GPU
    list_shared_GPU = SHARED_GPU
    list_free_GPU = FREE_GPU
    list_occupied_GPU = OCCUPIED_GPU
    list_user_id = LIST_USER
    dict_user_priority = PRIORITY
    dict_allocated_GPU_user = ALLOCATED_GPU_USER

    sender = 'O-CNO'
    receiver_uc1 = 'UC_1'
    receiver_uc2 = 'SS-CNO-UC2-MC'
    #num_GPU = len(list_free_GPU)
    num_GPU = 2


    input('\nPress enter for O-CNO to send GPU availability to UC_1...')
    producer = start_kafka_producer()
    write_decision_to_kafka(producer, sender, receiver_uc1, num_GPU)
    print('O-CNO --> SS-CNO (UC1): you can use up to {} GPU(s).'.format(num_GPU))

    o_cno_arbitration(list_GPU_id, dict_reserved_GPU, list_shared_GPU, list_free_GPU,\
                list_occupied_GPU, list_user_id, dict_user_priority,\
                dict_allocated_GPU_user, producer)
