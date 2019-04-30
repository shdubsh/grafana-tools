import json
import os
from get_metric_names import regex_extract_metrics, get_dashboards, get_dashboard
from config import Config

DASHBOARD_CHANGED = False
CONFIG = Config('./config.yaml')
WRITE_DIR = 'new-dashboards'


def update_dashboard(dashboard: dict):
    if dashboard.get('dashboard'):
        if dashboard['dashboard'].get('panels'):
            update(dashboard['dashboard']['panels'])


def update(panels):
    """
    There are several things to do here:
    1. Does this panel have sub-panels?  If so, call again with new panels base.
    2. If there are expr in the targets, determine:
      a. Does the expr have the old metric name in it?  If so, save a copy
         of the original and rewrite it with the new mapping.
      b. Does the expr use 'or' to attempt backwards-compatibility?
      c.
    :param panels: dict
    :return: None
    """
    global DASHBOARD_CHANGED
    for panel in panels:
        if panel.get('panels'):
            update(panel['panels'])  # Recursion
        if panel.get('targets'):
            for target in panel['targets']:
                if target.get('expr'):
                    expr = rewrite_expr(target['expr'])
                    original = target['expr']
                    if original != expr:
                        DASHBOARD_CHANGED = True
                        target['expr'] = make_backwards_compatible(expr, original)


def rewrite_expr(expr):
    """
    Iterate over mappings and replace old names with new names
    :param expr: str
    :return: str
    """
    for key in CONFIG.mappings.keys():
        metric_names = regex_extract_metrics(expr)
        if key in metric_names and CONFIG.mappings[key] not in metric_names:
            expr = expr.replace(key, CONFIG.mappings[key])
    return expr


def make_backwards_compatible(expr, original):
    """
    Attempt to make query backwards-compatible.
    If there is no 'or' in the query
    1. Function calls that fully encapsulate the query can be simply joined
    2. Metrics with no modifiers can be simply joined
    3. All others should be wrapped in parenthesis
    :param expr: str
    :param original: str
    :return: str
    """
    if len(expr.split(' or ')) < 2:
        if expr.split('(')[0] in CONFIG.blacklist \
                and expr[-1] == ')':
            return expr + ' or ' + original
        if (expr.count('{') + expr.count('}')) == 2 \
                and expr.split('(')[0] not in CONFIG.blacklist \
                and expr.strip()[-1] == '}':
            return expr + ' or ' + original
        return '({}) or ({})'.format(expr, original)


def write_dashboard(filename, dashboard):
    with open('{}/{}'.format(WRITE_DIR, filename), 'w') as f:
        f.write(json.dumps(dashboard))


def main():
    global DASHBOARD_CHANGED
    if not os.path.isdir(WRITE_DIR):
        os.mkdir(WRITE_DIR)
    for filename in get_dashboards():
        DASHBOARD_CHANGED = False  # Reset
        dashboard = get_dashboard(filename)
        update_dashboard(dashboard)
        if DASHBOARD_CHANGED:
            write_dashboard(filename, dashboard)


if __name__ == '__main__':
    main()

