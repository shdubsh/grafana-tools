Prometheus Metric Usage in Grafana
===

These scripts are for getting information about metrics usage in Wikimedia's Grafana instance.

Note: These scripts were developed against python 3.7, but should work in 3.x.

cache_dashboards.py
---
Downloads the dashboard json definition and caches it in `dashboards/`

Usage: `python3 src/cache_dashboards.py`

get_metric_names.py
---
Parses the cached dashboards and extracts the metric names from the Prometheus query.

Note: This requires the string 'prometheus' in the datasource name.

Usage: `python3 src/get_metric_names.py | sort | uniq > OUT_FILE`

left_not_in_right.py
---
Takes two newline-delimited files and reports on lines in the left file that are not in the right file.

Usage: `python3 src/left_not_in_right.py LEFT_FILE RIGHT_FILE`
 