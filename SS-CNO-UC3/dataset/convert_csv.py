import csv
import random
#from decimal import Decimal

# how to ramp up iperf traffic for creating congestion
START_IPERF_VAL = 50
STEP_IPERF = 1
NUM_RAMP_UP_POINT = 60

#congestion with 10% probability
CONG_PROB = 0

# number of look-ahead point to determine of congestion or not
LOOK_AHEAD = 50 # LOOK_AHEAD has to be less than NUM_RAMP_UP_POINT

# number of points in each row of dataset
NUM_SAMPLE_POINT = 10

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

if __name__ == '__main__':    
    num_sample = 10

    training_csv_file = 'training_data/train_input_new.csv'
    testing_csv_file = 'testing_data/test_input_new.csv'    

    list_test_input = []
    f = open('training_data/train_input.csv', 'r')
    for x in f.readlines():
        list_test_input.append(x.strip().split(','))
    f.close()
    with open(training_csv_file, 'w') as csvfile:   
        field_name = []
        for i in range(0, num_sample):
            field_name.append('point_' + str(i))
        field_name.append('congestion')
        writer = csv.DictWriter(csvfile, fieldnames = field_name)
        writer.writeheader()
        dic_data_row = {}
        for l in list_test_input:
            for j in range(0, num_sample):
                dic_data_row['point_' + str(j)] = l[j]
            dic_data_row['congestion'] = l[10]
            writer.writerow(dic_data_row)


    list_test_input = []
    f = open('testing_data/test_input.csv', 'r')
    for x in f.readlines():
        list_test_input.append(x.strip().split(','))
    f.close()
    with open(testing_csv_file, 'w') as csvfile:   
        field_name = []
        for i in range(0, num_sample):
            field_name.append('point_' + str(i))
        field_name.append('congestion')
        writer = csv.DictWriter(csvfile, fieldnames = field_name)
        writer.writeheader()
        dic_data_row = {}
        for l in list_test_input:
            for j in range(0, num_sample):
                dic_data_row['point_' + str(j)] = l[j]
            dic_data_row['congestion'] = l[10]
            writer.writerow(dic_data_row)
