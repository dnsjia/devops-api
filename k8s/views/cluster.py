import logging
import os

from kubernetes import client, config
from kubernetes.client import ApiException

from devops.settings import BASE_DIR



k8s_api_config = os.path.join(BASE_DIR, 'api', 'utils', 'config_test')
config.load_kube_config(config_file=k8s_api_config,)
logger = logging.getLogger('default')
app_v1 = client.CoreV1Api()
logger.info("Getting k8s nodes...")

response = app_v1.list_node()
# print(response)





nodes = []
for node in response.items:
        print(node)
#print("Current k8s node count is {}".format(len(response.items)))
#print(response.items)
