from jinja2 import Template
import jmespath
import json
import logging
import os
import requests
import time

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

MORPHEUS_TOKEN = os.environ.get('MORPHEUS_TOKEN')
MORPHEUS_URL = os.environ.get('MORPHEUS_URL')
TASK_NAME = os.environ.get('TASK_NAME')
CLUSTER_NAME = os.environ.get('CLUSTER_NAME')
ENVIRONMENT = os.environ.get('ENV')


def get_morpheus_auth():
    return {'Authorization': 'Bearer %s' % MORPHEUS_TOKEN}


def get_api(resource, resource_name, result_type=None, parameter=None):
    if result_type is None:
        result_type = resource
    logging.info('Get %s ID for %s' % (
        resource, resource_name
    ))
    resource_id, offset, total = None, 0, 1
    while not (total <= offset or resource_id):
        api_url = '%s/api/%s?max=100&offset=%s' % (MORPHEUS_URL, resource, offset)
        if parameter:
            api_url = api_url + '&' + parameter
        resource_list = json.loads(requests.get(
            api_url, headers=get_morpheus_auth()
        ).content.decode('UTF-8'))
        if result_type not in ['networks', 'resourcePools']:
            resource_id = jmespath.search(
                "%s[?name=='%s'] | [0].id" % (result_type, resource_name), resource_list
            )
        elif result_type == 'networks':
            resource_id = []
            for network in resource_name:
                id = jmespath.search(
                    "%s[?contains(name, '%s')] | [0].id" % (result_type, network),
                    resource_list
                )
                if id:
                    resource_id.append('network-' + str(id))
        elif result_type == 'resourcePools':
            resource_id = jmespath.search(
                "%s[?contains(externalId, '%s')] | [0].id" % (result_type, resource_name), resource_list
            )
        total = resource_list.get('meta', {}).get('total', 0)
        offset = offset + resource_list.get('meta', {}).get('size', 1)
    logging.info('The %s id is %s' % (resource, resource_id))
    return resource_id


def create_cluster_payload(cluster_name, env):
    with open('payloads/create_cluster.json') as payload, \
            open('config/config-api-mapping.json') as mapping, \
            open('config/%s-config.json' % env) as env_config:
        payload = Template(payload.read())
        mapping = json.loads(mapping.read())
        env_config = json.loads(env_config.read())
        data = {}
        for key, value in env_config.items():
            if key in mapping:
                key_mapping = mapping.get(key)
                url = key_mapping.get('path')
                if key == 'cluster_network_id':
                    url = url.replace("{{zone}}", str(data['cloud']))
                result_type = key_mapping.get('result_type')
                parameter_list = key_mapping.get('parameter')
                new_parameter = None
                if parameter_list:
                    for parameter in parameter_list:
                        if parameter == 'zone':
                            new_parameter = 'zoneId=%s' % data['cloud']
                value = get_api(url, value, result_type=result_type, parameter=new_parameter)
            data[key] = value
        data['cluster_name'] = cluster_name
        return payload.render(data).replace("'", '"')


def create_cluster(cluster_name):
    payload = json.loads(create_cluster_payload(cluster_name, ENVIRONMENT))
    print(json.dumps(payload, indent=4))
    api_response = requests.post(
        '%s/api/clusters' % MORPHEUS_URL,
        headers=get_morpheus_auth(),
        data=json.dumps(payload)
    )
    if api_response.status_code == 200:
        cluster_id = jmespath.search(
            'cluster.id',
            json.loads(api_response.content.decode('UTF-8'))
        )
        logging.info("Creating cluster with id %s", cluster_id)
        is_completed = False
        while not is_completed:
            time.sleep(300)
            cluster_details = requests.get(
                '%s/api/clusters/%s' % (MORPHEUS_URL, cluster_id),
                headers=get_morpheus_auth()
            )
            status = jmespath.search(
                'cluster.status', json.loads(cluster_details.content.decode('UTF-8'))
            )
            print(status)
            if status != 'provisioning':
                is_completed = True
    else:
        logging.error("Cluster Creation failed with error %s" % api_response.content.decode('UTF-8'))


cluster = get_api('clusters', 'test_d_cluster_0012')
if not cluster:
    create_cluster('test_d_cluster_0012')
