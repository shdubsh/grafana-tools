#!/bin/bash
for FILE in $(ls new-dashboards); do echo $FILE '#######################################################################' && diff <(jq -S . dashboards/$FILE) <(jq -S . new-dashboards/$FILE); done
