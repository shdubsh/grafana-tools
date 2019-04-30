import json
import os
import re
from config import Config


CONFIG = Config('config.yaml')
PATTERN = re.compile('([a-zA-Z0-9]+(_[a-zA-Z0-9]+)+)')


def get_dashboards():
    return os.listdir('dashboards')


def get_dashboard(filename):
    with open('dashboards/{}'.format(filename), 'r') as f:
        return json.loads(f.read())


def get_panels(dashboard):
    if dashboard.get('dashboard'):
        if dashboard['dashboard'].get('panels'):
            return dashboard['dashboard']['panels']
    return []


def has_prometheus(panel):
    if panel.get('datasource'):
        return 'prometheus' in panel['datasource']


def regex_extract_metrics(expr):
    matches = PATTERN.findall(expr)
    if matches:
        # parentheses denote a match group and findall will yield a list of tuples containing match groups.
        # the first match group contains what we want
        return [x[0] for x in matches]
    return []


if __name__ == '__main__':
    if not os.path.isdir('dashboards'):
        print('dashboards cache not found.  run cache_dashboards.py')
        exit(1)
    for filename in get_dashboards():
        for panel in get_panels(get_dashboard(filename)):
            if has_prometheus(panel):
                for target in panel['targets']:
                    for metric in regex_extract_metrics(target['expr']):
                        if metric not in CONFIG.blacklist:
                            print(metric)
