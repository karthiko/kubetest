import jmespath
import json
import logging
import requests
import subprocess

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)


def get_morpheus_credentials():
    return {
        "appliance_url": morpheus["morpheus"]["applianceUrl"],
        "morpheus_token": morpheus["morpheus"]["apiAccessToken"]
    }


credentials = get_morpheus_credentials()
MORPHEUS_TOKEN = credentials.get('morpheus_token')
MORPHEUS_URL = credentials.get('appliance_url')


def get_morpheus_auth():
    return {'Authorization': 'Bearer %s' % MORPHEUS_TOKEN}


def get_cluster_id(cluster_name):
    logging.info("Get Cluster ID for %s" % cluster_name)
    cluster_list = requests.get('%s/api/clusters' % MORPHEUS_URL, headers=get_morpheus_auth()).content.decode('UTF-8')
    cluster_id = jmespath.search(
        "clusters[?name=='%s'] | [0].id" % cluster_name, json.loads(cluster_list)
    )
    logging.info("The cluster id is %s" % cluster_id)
    return cluster_id


def get_kube_config(cluster_name):
    cluster_id = get_cluster_id(cluster_name)
    config_response = requests.get('%s/api/clusters/%s/api-config' % (MORPHEUS_URL, cluster_id),
                                   headers=get_morpheus_auth())
    config_json = json.loads(config_response.content.decode('UTF-8')).get('serviceAccess')
    with open("kubeconfig.conf", "w") as text_file:
        text_file.write("%s" % config_json)
    logging.info("Kube config of cluster %s copied to kubeconfig.conf" % cluster_name)


def get_blueprint_id(blueprint_name):
    logging.info("Get blueprint ID for %s" % blueprint_name)
    blueprint_id, offset, total = None, 0, 1
    while not (total <= offset or blueprint_id):
        blueprint_list = json.loads(requests.get(
            '%s/api/blueprints?offset=%s' % (MORPHEUS_URL, offset),
            headers=get_morpheus_auth()
        ).content.decode('UTF-8'))
        blueprint_id = jmespath.search(
            "blueprints[?name=='%s'] | [0].id" % blueprint_name, blueprint_list
        )
        total = blueprint_list.get('meta').get('total')
        offset = offset + blueprint_list.get('meta').get('size')
    logging.info("The blueprint id is %s" % blueprint_id)
    return blueprint_id


def get_deployment_yaml(blueprint_name):
    blueprint_id = get_blueprint_id(blueprint_name)
    logging.info("The blueprint id is %s" % blueprint_id)
    spec_response = requests.get('%s/api/blueprints/%s' % (MORPHEUS_URL, blueprint_id), headers=get_morpheus_auth())
    spec_json_response = json.loads(spec_response.content.decode('UTF-8'))
    spec_file = jmespath.search('blueprint.config.kubernetes.yaml', spec_json_response)
    with open("deployment.yaml", "w") as text_file:
        text_file.write("%s" % spec_file)
    logging.info("Deployment configuration from blueprint %s copied to deployment.conf" % blueprint_name)


if __name__ == "__main__":
    blueprint_name = morpheus['customOptions'].get('blueprint_name')
    cluster_name = morpheus['customOptions'].get('cluster_name')
    task = morpheus['customOptions'].get('task')
    kube_script = 'kubectl apply -f deployment.yaml --kubeconfig kubeconfig.conf'
    script = "helm repo add splunk-otel-collector-chart https://signalfx.github.io/splunk-otel-collector-chart; helm repo update; helm install --set cloudProvider='aws' --set distribution='eks' --set splunkObservability.accessToken='RlZv-HI8OI9gz5FCeWFKqA' --set clusterName='%s' --set splunkObservability.realm='us1' --set gateway.enabled='false' --generate-name splunk-otel-collector-chart/splunk-otel-collector --kubeconfig kubeconfig.conf" % cluster_name
    try:
        get_kube_config(cluster_name)
        if task == 'deployment':
            get_deployment_yaml(blueprint_name=blueprint_name)
            script = kube_script
        subprocess.run(
            script, shell=True, check=True, stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        logging.error("update cluster failed with error {}".format(e.stderr))