#!/bin/bash

mkdir -p output/local
TIMESTAMP=$(date +%Y%m%d%H%M%S) OUTPUT_DIR=output/local docker compose -f docker-compose.yml up --build
