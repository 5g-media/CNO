# =================================
# GPU management
# =================================
GPU_ID = ['GPU_1', 'GPU_2']
# UC_1: list of reserved GPUs
RESERSED_GPU = {'UC_1': ['GPU_1'], 'SS-CNO-UC2-MC': []}
# list of GPU shared between use cases
SHARED_GPU = ['GPU_2']
# list of GPUs currently are free
FREE_GPU = ['GPU_1', 'GPU_2']
# list of GPUs currently are occupied
OCCUPIED_GPU = []
# ===================================
# user request priority
# higher number means higher priority
# ===================================
LIST_USER = ['UC_1', 'SS-CNO-UC2-MC']
PRIORITY = {'UC_1': 1, 'SS-CNO-UC2-MC': 2}
ALLOCATED_GPU_USER = {}