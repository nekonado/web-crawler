#!/bin/bash

mkdir -p output
TIMESTAMP=$(date +%Y%m%d%H%M%S) docker compose -f docker-compose.yml up --build
