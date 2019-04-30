import requests
from time import sleep
import json
import os
from config import Config

CONFIG = Config('config.yaml')


def get_dashboards():
    url = '{}/api/search?query=&starred=false'.format(CONFIG.grafana_host)
    return requests.get(url).json()


def get_dashboard(uid):
    if uid not in CONFIG.excluded_dashboards:
        url = '{}/api/dashboards/uid/{}'.format(CONFIG.grafana_host, uid)
        return requests.get(url).json()


if __name__ == '__main__':
    if not os.path.isdir('dashboards'):
        os.mkdir('dashboards')
    exclude_list = [x.split('.')[0] for x in os.listdir('dashboards')]
    for d in get_dashboards():
        if d['uid'] not in exclude_list:
            with open('dashboards/{}.json'.format(d['uid']), 'w') as f:
                f.write(json.dumps(get_dashboard(d['uid'])))
            sleep(0.5)
