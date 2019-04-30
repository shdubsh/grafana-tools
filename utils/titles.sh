#!/bin/bash
for FILE in $(ls new-dashboards); do cat new-dashboards/$FILE | jq .dashboard.title; done
