import json
import os
from string import ascii_letters, digits
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
    expr = cleanup_duplicate(expr)
    metric_names = regex_extract_metrics(expr)
    for metric_name in [x['old'] for x in CONFIG.scalings]:
        if metric_name in metric_names:
            expr = update_scaling(metric_name, expr)
    for metric_name in [x['old'] for x in CONFIG.query_parameters]:
        if metric_name in metric_names:
            expr = update_query_parameters(metric_name, expr)
    for key in CONFIG.mappings.keys():
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


def cleanup_duplicate(expr):
    for idx in range(0, len(expr)):
        if expr[0:idx] == expr[idx:]:
            expr = expr[0:idx]
    return expr


def update_scaling(metric_name, expr):
    new_metric_name, factor = [(x['new'], x['factor']) for x in CONFIG.scalings if x['old'] == metric_name][0]
    # Bypass if already backwards-compatibile
    if new_metric_name in expr:
        return expr
    # HACK
    # By observing what is in dashboards right now, there are no other instances of scaling.
    # This hack will simply clobber them.
    try:
        expr.index(' / 1000')
        expr = expr.replace(' / 1000', '')
        return expr.replace(metric_name, new_metric_name)
    except ValueError:
        pass
    try:
        expr.index('/10')
        expr = expr.replace('/10', '*100')
        return expr.replace(metric_name, new_metric_name)
    except ValueError:
        pass
    # /HACK
    occurrences = expr.count(metric_name)
    beginning = 0
    for _ in range(0, occurrences):
        beginning = expr.index(metric_name, beginning)
        end = expr.index('}', beginning) + 1
        try:
            placement = expr.index(')', end) + 1
            expr = expr[:placement].replace(metric_name, new_metric_name) + '{}'.format(factor) + expr[placement:]
        except ValueError:
            expr = expr.replace(metric_name, new_metric_name) + '{}'.format(factor)
    return expr


def extract_params(source):
    output = {}
    for param in source.split(','):
        operator = ''
        key_end_position = 0
        value_start_position = 0
        for idx, char in enumerate(param):
            if operator:
                if char in ['\'', '"']:
                    value_start_position = idx
                    break
                else:
                    operator += char
                    continue
            if char not in ascii_letters + digits:
                key_end_position = idx
                operator += char
        output[param[0:key_end_position]] = {
            'operator': operator,
            'value': param[value_start_position:].replace('\'', '').replace('"', '')
        }
    return output


def update_query_parameters(metric_name, expr):
    # Bypass if already backwards-compatibile
    for old, new in [(x['old'], x['new']) for x in CONFIG.query_parameters]:
        if metric_name == old:
            if type(new) == list:
                for new_metric_name in new:
                    if new_metric_name in expr:
                        return expr
            else:
                if new in expr:
                    return expr
    occurrences = expr.count(metric_name)
    beginning = 0
    for _ in range(0, occurrences):
        beginning = expr.index(metric_name, beginning)
        labels_begin = expr.index('{', beginning) + 1
        end = expr.index('}', beginning)
        params = extract_params(expr[labels_begin:end])
        # HACK
        # I don't want to write a data-driven expression language at this time.  Thanks for asking.
        new_metric_name = metric_name
        if metric_name == 'node_cpu':
            new_metric_name = 'node_cpu_seconds_total'
            if params.get('cpu'):
                params['cpu']['value'] = params['cpu']['value'].replace('cpu', '')
            if params.get('mode'):
                if params['mode']['value'] == 'guest':
                    params['mode']['value'] = 'user'
                    new_metric_name = 'node_cpu_guest_seconds_total'
                if params['mode']['value'] == 'guest_nice':
                    params['mode']['value'] = 'nice'
                    new_metric_name = 'node_cpu_guest_seconds_total'
        if metric_name == 'node_nfs_procedures':
            new_metric_name = 'node_nfs_requests_total'
            if params.get('procedure'):
                if not params.get('method'):
                    params['method'] = {}
                params['method']['operator'] = params['procedure']['operator']
                params['method']['value'] = params['procedure']['value']
                del(params['procedure'])
            if params.get('version'):
                if not params.get('proto'):
                    params['proto'] = {}
                params['proto']['operator'] = params['version']['operator']
                params['proto']['value'] = params['version']['value']
                del(params['version'])

        expr = expr[0:beginning] \
            + expr[beginning:labels_begin-1].replace(metric_name, new_metric_name) \
            + '{' \
            + ','.join(['{}{}"{}"'.format(key, value['operator'], value['value']) for key, value in params.items()]) \
            + '}' \
            + expr[end+1:]
        # /HACK
    return expr


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

