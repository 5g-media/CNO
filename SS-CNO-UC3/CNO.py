from __future__ import absolute_import, division, print_function

import tensorflow as tf
import tensorflow.contrib.eager as tfe
#import numpy as np
import csv
from time import sleep
from daemon import start_kafka_producer, write_decision_to_kafka

import os
import sys
#from daemon import write_decision_to_kafka

'''
#########
from settings import METRIC_TEMPLATE

import json
from kafka import KafkaProducer
from settings import KAFKA_SERVER, KAFKA_API_VERSION, KAFKA_EXECUTION_TOPIC, METRIC_TEMPLATE, LOGGING


def generate_metric(metric_value, timestamp):
    metric = METRIC_TEMPLATE
    metric['execution']['planning'] = metric_value
    metric['execution']['timestamp'] = timestamp
    return metric

def start_kafka_producer():
    producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER, api_version=KAFKA_API_VERSION,
                                     value_serializer=lambda v: json.dumps(v).encode('utf-8'))
    return producer

#########
'''

# divide the real value of load to this number for nomalization task in ML
NORMALIZATION_PARA = 100.0

def parse_csv(line):

    int_num_sample = 10
    # sets field types
    example_defaults =[]

    for i in range(0, int_num_sample):
        example_defaults.append([0.])
    example_defaults.append([0])
    
    parsed_line = tf.decode_csv(line, example_defaults)
    # First int_num_sample fields are background, anomaly and video history
    features = tf.reshape(parsed_line[:-1], shape=(int_num_sample,))
    # Last field is the label
    label = tf.reshape(parsed_line[-1], shape=())
    return features, label

def loss(model, x, y):
    y_ = model(x)
    return tf.losses.sparse_softmax_cross_entropy(labels=y, logits=y_)


def grad(model, inputs, targets):
    with tfe.GradientTape() as tape:
        loss_value = loss(model, inputs, targets)
    return tape.gradient(loss_value, model.variables)

# create list to test from csv file, to see in detail each row of test, which 
# one is correct
def find_list_to_test_from_csv(csv_test_file):
    list_to_test = []
    list_to_test_with_prediction_val = []
    with open(csv_test_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            tmp_list = []
            tmp_list_with_prediction = []
            
            for i in range(0, 10):
                if 'point_' + str(i) not in row.keys():
                    return list_to_test, list_to_test_with_prediction_val
                tmp_list.append(round(float(row['point_' + str(i)])/NORMALIZATION_PARA, 2))
                tmp_list_with_prediction.append(round(float(row['point_' + str(i)])/NORMALIZATION_PARA,2))
                
            list_to_test.append(tmp_list)
            tmp_list_with_prediction.append(float(row['congestion']))
            list_to_test_with_prediction_val.append(tmp_list_with_prediction)
            
    return list_to_test, list_to_test_with_prediction_val


# load model from checkpoint file, no need to train the model
def load_model():
    int_num_sample = 10    
    # dataset for training and testing
    test_fp = './dataset/testing_data/test_input.csv'
    train_dataset_fp = './dataset/training_data/train_input.csv'

    # set number of epochs to train the system
    #num_epochs = 100
    
    tf.enable_eager_execution()
    
    model = tf.keras.Sequential([
      tf.keras.layers.Dense(512, activation="relu", input_shape=(int_num_sample,)),  # input shape required
      tf.keras.layers.Dense(512, activation="relu"),
      tf.keras.layers.Dense(2)
      #tf.keras.layers.Dense(2, activation="softmax")
    ])
    
    #optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.01)
    optimizer = tf.train.AdamOptimizer()
    
    # prepare to save a checkpoint of the model, save the model for every 
    # training loop 
    checkpoint_dir = './checkpoint_file'
    checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt")
    latest_cpkt = tf.train.latest_checkpoint(checkpoint_dir)
    root = tfe.Checkpoint(optimizer=optimizer, model=model)    
    root.restore(latest_cpkt).run_restore_ops(session=None)
    

    test_dataset = tf.data.TextLineDataset(test_fp)
    test_dataset = test_dataset.skip(1)             # skip header row
    test_dataset = test_dataset.map(parse_csv)      # parse each row with the function created earlier
    test_dataset = test_dataset.shuffle(1000)       # randomize
    test_dataset = test_dataset.batch(32)           # use the same batch size as the training set
    
    test_accuracy = tfe.metrics.Accuracy()
    
    for (x, y) in tfe.Iterator(test_dataset):
        #x = x/100.0
        prediction = tf.argmax(model(x), axis=1, output_type=tf.int32)
        test_accuracy(prediction, y)
    
    print("Test set accuracy: {:.3%}".format(test_accuracy.result()))
    producer = start_kafka_producer()
    while (1):
        file_monitoring = '../file_monitoring.csv'
        list_to_test = []
        list_to_test, list_to_test_with_prediction_val = \
            find_list_to_test_from_csv(file_monitoring)
        if list_to_test == []:
            continue
        
        predict_dataset = tf.convert_to_tensor(list_to_test)
    
        predictions = model(predict_dataset)
        for i, logits in enumerate(predictions):        
            class_idx = tf.argmax(logits).numpy()
            print(list_to_test[i], class_idx)
            if class_idx == 1:
                print('*********** vnf_scale_out **********')
                write_decision_to_kafka(producer, 'vnf_scale_out')
                exit()
                #sleep(10)
            else:
                print('------ do nothing -----')
                #write_decision_to_kafka(producer, 'do_nothing')
            
        sleep(1)

def train_and_save_checkpoint():
    
    int_num_sample = 10
    
    # dataset for training and testing
    test_fp = './dataset/testing_data/test_input.csv'
    train_dataset_fp = './dataset/training_data/train_input.csv'

    # set number of epochs to train the system
    num_epochs = 100
    
    tf.enable_eager_execution()
    
    train_dataset = tf.data.TextLineDataset(train_dataset_fp)
    train_dataset = train_dataset.skip(1)             # skip the first header row
    train_dataset = train_dataset.map(parse_csv)      # parse each row
    train_dataset = train_dataset.shuffle(buffer_size=1000)  # randomize
    train_dataset = train_dataset.batch(32)
    
    
    # View a single example entry from a batch
    features, label = tfe.Iterator(train_dataset).next()
    ##print("example features:", features[0])
    ##print("example label:", label[0])
    
    model = tf.keras.Sequential([
      tf.keras.layers.Dense(512, activation="relu", input_shape=(int_num_sample,)),  # input shape required
      tf.keras.layers.Dense(512, activation="relu"),
      tf.keras.layers.Dense(2)
      #tf.keras.layers.Dense(2, activation="softmax")
    ])
    
    #optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.01)
    optimizer = tf.train.AdamOptimizer()
    
    # prepare to save a checkpoint of the model, save the model for every 
    # training loop 
    checkpoint_dir = './checkpoint_file'
    checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt")
    root = tfe.Checkpoint(optimizer=optimizer, model=model)
    
    # keep results for plotting
    train_loss_results = []
    train_accuracy_results = []
    
    
    for epoch in range(num_epochs):
        epoch_loss_avg = tfe.metrics.Mean()
        epoch_accuracy = tfe.metrics.Accuracy()
    
        # Training loop - using batches of 32
        for x, y in tfe.Iterator(train_dataset):
            #x = x/100.0
            #print(x)
            # Optimize the model
            grads = grad(model, x, y)
            optimizer.apply_gradients(zip(grads, model.variables),
                            global_step=tf.train.get_or_create_global_step())
    
            # Track progress
            epoch_loss_avg(loss(model, x, y))  # add current batch loss
            # compare predicted label to actual label
            epoch_accuracy(tf.argmax(model(x), axis=1, output_type=tf.int32), y)            
    
         # end epoch
        train_loss_results.append(epoch_loss_avg.result())
        train_accuracy_results.append(epoch_accuracy.result())
      
        if epoch % 10 == 0:
            print("Epoch {:03d}: Loss: {:.3f}, Accuracy: {:.3%}".format(epoch,
                                                      epoch_loss_avg.result(),
                                                      epoch_accuracy.result()))
    # save checkpoint model
    root.save(file_prefix=checkpoint_prefix)

    test_dataset = tf.data.TextLineDataset(test_fp)
    test_dataset = test_dataset.skip(1)             # skip header row
    test_dataset = test_dataset.map(parse_csv)      # parse each row with the function created earlier
    test_dataset = test_dataset.shuffle(1000)       # randomize
    test_dataset = test_dataset.batch(32)           # use the same batch size as the training set
    
    test_accuracy = tfe.metrics.Accuracy()
    
    for (x, y) in tfe.Iterator(test_dataset):
        #x = x/100.0
        prediction = tf.argmax(model(x), axis=1, output_type=tf.int32)
        test_accuracy(prediction, y)
    
    print("Test set accuracy: {:.3%}".format(test_accuracy.result()))
    producer = start_kafka_producer()
    while (1):
        file_monitoring = '../file_monitoring.csv'
        list_to_test = []
        list_to_test, list_to_test_with_prediction_val = \
            find_list_to_test_from_csv(file_monitoring)

        if list_to_test == []:
            continue
            
        predict_dataset = tf.convert_to_tensor(list_to_test)
    
        predictions = model(predict_dataset)
        for i, logits in enumerate(predictions):        
            class_idx = tf.argmax(logits).numpy()
            print(list_to_test[i], class_idx)
            if class_idx == 1:
                print('*********** vnf_scale_out **********')
                write_decision_to_kafka(producer, 'vnf_scale_out')
                exit()
                #sleep(10)
            else:
                print('------ do nothing -----')
                #write_decision_to_kafka(producer, 'do_nothing')
            
        sleep(1)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'load':
            load_model()
        else:
            print('**** wrong argument, should be \'load\' or nothing')
    else:
        train_and_save_checkpoint()
    
