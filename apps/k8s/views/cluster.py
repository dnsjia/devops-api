import logging
from kubernetes import client, config
from kubernetes.client import models
import yaml
# from devops.settings import BASE_DIR
# k8s_api_config = os.path.join(BASE_DIR, 'apps', 'utils', 'config_test')

config.load_kube_config(config_file=None)
logger = logging.getLogger('default')
app_v2 = client.CoreV1Api()
app_v1 = client.AppsV1Api()
logger.info("Getting k8s nodes...")

res = app_v2.list_event_for_all_namespaces(field_selector="involvedObject.kind=Deployment,"
                                                          "involvedObject.name=v3-release")

print(res)

# re = yaml.safe_dump(res.to_dict(), sort_keys=False)
# print(re)

# print(yaml.safe_load(re))



