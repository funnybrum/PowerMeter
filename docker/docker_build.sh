#!/bin/bash

cd ..
docker build -f ./docker/Dockerfile . -t power_meter
cd docker
