from os import path, pardir

PROJECT_ROOT = '/opt/o-cno-arbitrator'

# =================================
# KAFKA SETTINGS
# =================================
KAFKA_SERVER = '217.172.11.173:9092'
KAFKA_CLIENT_ID = 'o-cno-arbitrator'
KAFKA_API_VERSION = (0, 10, 1)
KAFKA_OCNO_TOPIC = "cno"

# ===================================
# MSG BETWEEN SS-CNO (UC1) <--> O-CNO
# ===================================

REQUEST_TEMPLATE = {
    "sender": "O-CNO",        
    "receiver": "UC_1",        
    "resource": {
        "GPU": 1,
        "CPU": 0,
        "RAM": None,
        "disk": None,
        "bw": None
     },
   "option": None
}

# ===================================
# MSG BETWEEN SS-CNO (UC2) <--> O-CNO
# ===================================

SS_CNO_UC2_OCNO = {
    "sender": "O-CNO",        
    "receiver": "UC_1",        
    "resource": {
        "GPU": 1,
        "CPU": 0,
        "RAM": None,
        "disk": None,
        "bw": None
     },
   "option": None,
   "nfvi": None
}

# ========================================
# MSG from Edge selector --> SS-CNO (UC2)
# ========================================

EDGE_SELECTOR_REQ = {
    "sender": "edge-selector",
    "receiver": "SS-CNO-UC2-MC",
    "session_uuid": "123abc",
    "payload": {
        # function_values can be out from: 'vspeech', 'vspeech_vdetection', 'vdetection', 'none'
         # none - means just the
        "function": "vspeech_vdetection",
         # mode_values = ['safe-remote', 'live-remote', 'safe-local']
        "mode": "safe-local",
         # descending order of geolocation
         # empty list would considered as wild card
         "nfvi_uuid_list": [
           "tid",
           "ncsrd",
           "ote"
         ]
     }
}

# =======================================
# MSG from SS-CNO (UC2) --> Edge selector
# =======================================

EDGE_SELECTOR_RESPONSE = {
    "sender": "SS-CNO-UC2-MC",
    "receiver": "edge-selector",
    "session_uuid": "123abc",
    "resource": {
        "GPU": ['vspeech', 'vdetection'],
        "CPU": [],
        "nfvi_uuid": "tid"
     }
}