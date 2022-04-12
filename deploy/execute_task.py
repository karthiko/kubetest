from jinja2 import Template
import jmespath
import json
import logging
import os
import requests

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

MORPHEUS_TOKEN = os.environ.get('MORPHEUS_TOKEN')
MORPHEUS_URL = os.environ.get('MORPHEUS_URL')


def get_morpheus_auth():
    return {'Authorization': 'Bearer %s' % MORPHEUS_TOKEN}


def get_task_id(task_name):
    logging.info("Get task ID for %s" % task_name)
    task_id, offset, total = None, 0, 1
    while not (total <= offset or task_id):
        task_list = json.loads(requests.get(
            '%s/api/tasks?offset=%s' % (MORPHEUS_URL, offset),
            headers=get_morpheus_auth()
        ).content.decode('UTF-8'))
        task_id = jmespath.search(
            "tasks[?name=='%s'] | [0].id" % task_name, task_list
        )
        total = task_list.get('meta').get('total')
        offset = offset + task_list.get('meta').get('size')
    logging.info("The task_ id is %s" % task_id)
    return task_id


def execute_task(task='deployment'):
    task_name = os.environ.get('TASK_NAME')
    task_id = get_task_id(task_name)
    with open("payloads/execute_task.json", "r") as execute_task_stream:
        try:
            data = {
                "cluster_name": os.environ.get('CLUSTER_NAME'),
                "blueprint_name": os.environ.get('BLUEPRINT_NAME'),
                "environment": os.environ.get('ENVIRONMENT'),
                "task": task
            }
            execute_task_payload = Template(execute_task_stream.read())
            api_response = requests.put(
                    '%s/api/tasks/%s/execute' % (MORPHEUS_URL, task_id),
                    headers=get_morpheus_auth(),
                    data=execute_task_payload.render(data)
                )
            logging.info("Task triggered %s" % api_response.content)
        except Exception as e:
            logging.error("Error in triggering task execution %s" % e)


execute_task()
