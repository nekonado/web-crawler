#!/bin/bash

mkdir -p output/local
OUTPUT_DIR=output/local docker compose -f docker-compose.yml up --build
