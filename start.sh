#!/bin/bash
# Remove the volume if it exists
docker container rm -f dol-loki
docker volume rm dol-loki-data --force || true
docker compose up -d
