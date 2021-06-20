from hikaru.model import *
from kubernetes import config

config.load_kube_config()
try:
    x= ConfigMap.readNamespacedConfigMap("doesnt-exist", "robusta").obj
except Exception as e:
    pass
