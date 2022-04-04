import jmespath
import json
import logging
import os
import requests
import yaml

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

MORPHEUS_TOKEN = os.environ.get('MORPHEUS_TOKEN')
MORPHEUS_URL = os.environ.get('MORPHEUS_URL')
BLUEPRINT_NAME = os.environ.get('BLUEPRINT_NAME')


def get_morpheus_auth():
    return {'Authorization': 'Bearer %s' % MORPHEUS_TOKEN}


def get_deployment_config():
    with open("online-boutique/deployment.yaml", "r") as stream:
        try:
            test = list(yaml.safe_load_all(stream))
            deployment_file = yaml.dump_all(test, sort_keys=False)
            return deployment_file
        except yaml.YAMLError as exc:
            logging.error("Error in reading the deployment configuration %s" % exc)
            return None


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


def update_blueprint(blueprint_name):
    blueprint_id = get_blueprint_id(blueprint_name)
    with open("deploy/payloads/app_blueprint.json", "r") as blueprint_payload_stream:
        try:
            blueprint_payload = json.load(blueprint_payload_stream)
            blueprint_payload['blueprint']['config']['kubernetes']['yaml'] = get_deployment_config()
            if blueprint_id:
                logging.info("Updating blueprint %s" % blueprint_name)
                config_response = requests.put(
                    '%s/api/blueprints/%s' % (MORPHEUS_URL, blueprint_id),
                    headers=get_morpheus_auth(),
                    data=json.dumps(blueprint_payload)
                )
                logging.info("Update blueprint response %s" % config_response.content)
            else:
                logging.info("Creating blueprint %s" % blueprint_name)
                config_response = requests.post(
                    '%s/api/blueprints' % MORPHEUS_URL,
                    headers=get_morpheus_auth(),
                    data=json.dumps(blueprint_payload)
                )
                logging.info("Create blueprint response %s" % config_response.content)
        except yaml.YAMLError as e:
            logging.error("Error in updating blueprint %s" % e)


update_blueprint(BLUEPRINT_NAME)