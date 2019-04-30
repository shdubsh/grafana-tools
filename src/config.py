import yaml
from string import ascii_letters, digits

# Valid metric names are letters, digits, and underscore
VALID_CHARACTERS = ascii_letters + digits + '_'


class Config:
    functions = []
    operators = []
    mappings = {}
    scalings = []
    query_parameters = []
    excluded_dashboards = []
    grafana_host = ''

    def __init__(self, config):
        with open(config, 'r') as f:
            parsed = yaml.safe_load(f.read())
        self.functions = parsed['functions']
        self.operators = parsed['operators']
        self.mappings = parsed['mappings']
        self.scalings = parsed['scalings']
        self.query_parameters = parsed['query_parameters']
        self.excluded_dashboards = parsed['excluded_dashboards']
        self.grafana_host = parsed['grafana_host']

    @property
    def blacklist(self):
        return self.functions + self.operators
