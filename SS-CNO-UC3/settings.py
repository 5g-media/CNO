from os import path, pardir

#PROJECT_ROOT = "C:\\Users\\magni_000\\Documents\\PyCharm\\fivegmedia\\monitoring-data-translator"
# PROJECT_ROOT = '/opt/monitoring-data-translator'
PROJECT_ROOT = '/opt/cno_ml'
# =================================
# WHITE LIST OF MONITORING METRICS
# =================================
METRICS_WHITE_LIST = {
    "openstack": ['memory', 'memory.usage', 'memory.resident', 'memory.bandwidth.total', 'memory.bandwidth.local',
                  'memory.swap.in', 'memory.swap.out', 'cpu', 'cpu_util', 'cpu.delta', 'vcpus', 'cpu_l3_cache',
                  'network.incoming.bytes', 'network.incoming.bytes.rate', 'network.outgoing.bytes',
                  'network.outgoing.bytes.rate', 'network.incoming.packets', 'network.incoming.packets.rate',
                  'network.outgoing.packets', 'network.outgoing.packets.rate', 'network.incoming.packets.drop',
                  'network.outgoing.packets.drop', 'network.incoming.packets.error', 'network.outgoing.packets.error'],
    "vmware": ['', ],
    "opennebula": ['', ],
    "unikernels": ['', ],
    "kubernetes": ['', ],
    "elk": ['', ],
}

# =================================
# KAFKA SETTINGS
# =================================
#KAFKA_SERVER = 217.172.11.188:9092'
#KAFKA_CLIENT_ID = 'monitoring-data-translator'
KAFKA_SERVER = '217.172.11.173:9092'
KAFKA_CLIENT_ID = 'CNO_UC3_UCL'

KAFKA_API_VERSION = (0, 10, 1)
KAFKA_PREFIX_TOPIC = "devstack"  # "devstack.*"
#KAFKA_MONITORING_TOPICS = {"openstack": "nvfi.eng.openstack", "vmware": "vmware", }
KAFKA_MONITORING_TOPICS = {"uc3_translation": "ns.instances.trans", "uc3_raw": "app.vcache.metrics"}
KAFKA_TRANSLATION_TOPIC_SUFFIX = "trans"

KAFKA_EXECUTION_TOPIC = "ns.instances.exec"

# =================================
# OSM SETTINGS
# =================================
OSM_IP = "192.168.1.171"
OSM_ADMIN_CREDENTIALS = {"username": "admin", "password": "admin"}
OSM_COMPONENTS = {"UI": 'https://{}:8443'.format(OSM_IP),
                  "SO-API": 'https://{}:8008'.format(OSM_IP),
                  "RO-API": 'http://{}:9090'.format(OSM_IP)}

METRIC_TEMPLATE = {
    "vim": {
        "name": "dev-openstack",
        "type": "openstack"
    },
    "mano": {
        "vdu": {
            "id": "da6849d7-663f-4520-8ce0-78eaacf74f08",
            "flavor": {
                "name": "ubuntuvnf_vnfd-VM-flv",
                "ram": 4096,
                "id": "c46aecab-c6a9-4775-bde2-070377b8111f",
                "vcpus": 1,
                "disk": 10,
                "swap": 0,
                "ephemeral": 0
            },
            "image_id": "a46178eb-9f69-4e44-9058-c5eb5ded0aa3",
            "status": "running"
        },
        "vnf": {
            "id": "00fa217e-cf90-447a-975f-6d838e7c20ed",
            "nvfd_id": None
        },
        "ns": {
            "id": "abf07959-053a-4443-a96f-78164913277b",
            "nsd_id": None
        }
    },
    "metric": {
        "name": "network.incoming.packets.rate",
        "value": None,
        "timestamp": None,
        "type": "gauge",
        "unit": "Mbps"
    },
    "execution": {
        "name": "cno.scaling.decision",
        "planning": None,
        "timestamp": None,
        "type": "binary"
    }
}
# ==================================
# LOGGING SETTINGS
# ==================================
# See more: https://docs.python.org/3.5/library/logging.config.html
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'detailed': {
            'class': 'logging.Formatter',
            'format': "[%(asctime)s] - [%(name)s:%(lineno)s] - [%(levelname)s] %(message)s",
        },
        'simple': {
            'class': 'logging.Formatter',
            'format': '%(name)-15s %(levelname)-8s %(processName)-10s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
        },
        'translator': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "{}/logs/translator.log".format(PROJECT_ROOT),
            'mode': 'w',
            'formatter': 'detailed',
            'level': 'DEBUG',
            'maxBytes': 2024 * 2024,
            'backupCount': 5,
        },
        'soapi': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "{}/logs/soapi.log".format(PROJECT_ROOT),
            'mode': 'w',
            'formatter': 'detailed',
            'level': 'DEBUG',
            'maxBytes': 2024 * 2024,
            'backupCount': 5,
        },
        'errors': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "{}/logs/error.log".format(PROJECT_ROOT),
            'mode': 'w',
            'level': 'ERROR',
            'formatter': 'detailed',
            'maxBytes': 2024 * 2024,
            'backupCount': 5,
        },
    },
    'loggers': {
        'translator': {
            'handlers': ['translator']
        },
        'soapi': {
            'handlers': ['soapi']
        },
        'errors': {
            'handlers': ['errors']
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console']
    },
}
