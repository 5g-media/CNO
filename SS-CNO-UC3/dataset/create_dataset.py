import csv
import random
from statistics import mean
#from decimal import Decimal

# how to ramp up iperf traffic for creating congestion
START_IPERF_VAL = 50
STEP_IPERF = 1
NUM_RAMP_UP_POINT = 60
            
#congestion with 10% probability
CONG_PROB = 0
CONGESTION_THRESHOLD = 25
    
# number of look-ahead point to determine of congestion or not
LOOK_AHEAD = 50 # LOOK_AHEAD has to be less than NUM_RAMP_UP_POINT

# number of points in each row of dataset
NUM_SAMPLE_POINT = 10
NUM_MOVING_AVERAGE = 20

def create_training_dataset(list_all_data_point_origin, training_csv_file, num_sample):  

    list_all_data_point = list_all_data_point_origin.copy()
    list_congestion = [0]*len(list_all_data_point)   
    i = 0
    while i < len(list_all_data_point) - num_sample:
        # determining congestion with 10% probability
        step_increase = 0
        start_value = 0
        if random.randint(0, 101) > (100 - CONG_PROB):
            step_increase = STEP_IPERF
            start_value = START_IPERF_VAL
        for j in range(0, num_sample):
            list_all_data_point[i + j] += start_value + step_increase*(j+1)        

        if step_increase > 0:
            start_detect_congestion = i + (NUM_RAMP_UP_POINT - LOOK_AHEAD)
            end_detect_congestion = min(i + NUM_RAMP_UP_POINT, len(list_congestion))
            for j in range(start_detect_congestion, end_detect_congestion):
                list_congestion[j] = 1
        i += num_sample

    with open(training_csv_file, 'w') as csvfile:   
        field_name = []
        for i in range(0, num_sample):
            field_name.append('point_' + str(i))
        field_name.append('congestion')
        writer = csv.DictWriter(csvfile, fieldnames = field_name)
        writer.writeheader()
        dic_data_row = {}
                
        for i in range(0, len(list_all_data_point) - num_sample):            

            for j in range(0, num_sample):
                if j == 0:
                    dic_data_row['point_' + str(j)] = \
                                        round(list_all_data_point[i + j], 3)
                else:
                    dic_data_row['point_' + str(j)] = round(list_all_data_point[i + j] \
                                        - list_all_data_point[i + j - 1], 3)
            
            dic_data_row['congestion'] = list_congestion[i]                                                   
            writer.writerow(dic_data_row)  

def create_testing_dataset(list_all_data_point_origin, testing_csv_file, num_sample):  

    list_all_data_point = list_all_data_point_origin.copy()
    list_congestion = [0]*len(list_all_data_point)   
    i = 0
    while i < len(list_all_data_point) - num_sample:
        # determining congestion with 10% probability
        step_increase = 0
        start_value = 0
        if random.randint(0, 101) > (100 - CONG_PROB):
            step_increase = STEP_IPERF
            start_value = START_IPERF_VAL
        for j in range(0, num_sample):
            list_all_data_point[i + j] += start_value + step_increase*(j+1)        

        if step_increase > 0:
            start_detect_congestion = i + (NUM_RAMP_UP_POINT - LOOK_AHEAD)
            end_detect_congestion = min(i + NUM_RAMP_UP_POINT, len(list_congestion))
            for j in range(start_detect_congestion, end_detect_congestion):
                list_congestion[j] = 1
        i += num_sample

    with open(testing_csv_file, 'w') as csvfile:   
        field_name = []
        for i in range(0, num_sample):
            field_name.append('point_' + str(i))
        field_name.append('congestion')
        writer = csv.DictWriter(csvfile, fieldnames = field_name)
        writer.writeheader()
        dic_data_row = {}
                
        for i in range(0, len(list_all_data_point) - num_sample):            

            for j in range(0, num_sample):
                if j == 0:
                    dic_data_row['point_' + str(j)] = \
                                        round(list_all_data_point[i + j], 3)
                else:
                    dic_data_row['point_' + str(j)] = round(list_all_data_point[i + j] \
                                        - list_all_data_point[i + j - 1], 3)
            
            dic_data_row['congestion'] = list_congestion[i]                                                   
            writer.writerow(dic_data_row)  

def create_training_moving_average(real_load_file, num_moving_average, \
                                     training_csv_file, num_sample):
    list_load = []
    f = open(real_load_file, 'r')
    for x in f.readlines():
        list_load.append(float(x))
    f.close()

    with open(training_csv_file, 'w') as csvfile:   
        field_name = []
        for i in range(0, num_sample):
            field_name.append('point_' + str(i))
        field_name.append('congestion')
        writer = csv.DictWriter(csvfile, fieldnames = field_name)
        writer.writeheader()
        dic_data_row = {}

        for i in range(num_moving_average, len(list_load) - NUM_SAMPLE_POINT):
            for j in range(0, NUM_SAMPLE_POINT):
                dic_data_row['point_' + str(j)] = \
                                    round(mean(list_load[i - num_moving_average + j : i + j])/100.0, 2)
            
            if dic_data_row['point_9'] >= CONGESTION_THRESHOLD/100.0:
                dic_data_row['congestion'] = 1
            else:
                dic_data_row['congestion'] = 0

            writer.writerow(dic_data_row)

if __name__ == '__main__':    
    training_csv_file = 'training_data/train_input.csv'
    testing_csv_file = 'testing_data/test_input.csv'

#------------------------------------------------------------------------------
# create training data set
    list_all_data_point = []
    previous_point = 0
    current_point = 0
    #f = open('tmp.txt', 'r')

    # read kafka log file to extract data from edge cache, translate the raw 
    # data (accumulated traffic in kafka) into real load
    f = open('scenario2_with_iperf_2205_12.8Mbps.txt', 'r')
    for line in f:
        IP_address = line.split()[0] # only collect data for the edge cache
        if IP_address == '192.168.111.19':            
            if previous_point == 0:
                previous_point = float(line.split()[4])
                continue
            else:
                current_point = float(line.split()[4])
                list_all_data_point.append(round(current_point - previous_point,3))
                previous_point = current_point    
    f.close()

    # write real load into a file for using later
    f = open('log_real_load.txt', 'w')
    for v in list_all_data_point:
        f.write(str(v) + '\n')
    f.close()
    
    create_training_moving_average('log_real_load.txt', NUM_MOVING_AVERAGE,\
                         training_csv_file, NUM_SAMPLE_POINT)
#------------------------------------------------------------------------------
# create testing data set

    list_all_data_point = []
    previous_point = 0
    current_point = 0
    #f = open('tmp.txt', 'r')

    # read kafka log file to extract data from edge cache, translate the raw 
    # data (accumulated traffic in kafka) into real load
    f = open('scenario1_no_iperf_2205_12.8Mbps.txt', 'r')
    for line in f:
        IP_address = line.split()[0] # only collect data for the edge cache
        if IP_address == '192.168.111.19':            
            if previous_point == 0:
                previous_point = float(line.split()[4])
                continue
            else:
                current_point = float(line.split()[4])
                list_all_data_point.append(round(current_point - previous_point,3))
                previous_point = current_point    
    f.close()

    # write real load into a file for using later
    f = open('log_real_load.txt', 'w')
    for v in list_all_data_point:
        f.write(str(v) + '\n')
    f.close()

    create_training_moving_average('log_real_load.txt', NUM_MOVING_AVERAGE,\
                         testing_csv_file, NUM_SAMPLE_POINT)

    #create_training_dataset(list_all_data_point, training_csv_file,\
    #                         NUM_SAMPLE_POINT)
    #create_testing_dataset(list_all_data_point, testing_csv_file, NUM_SAMPLE_POINT)

