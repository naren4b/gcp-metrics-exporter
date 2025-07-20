# Set these variables as needed
IMAGE_NAME = copilot-metrics-exporter
TAG ?= latest
REGISTRY ?= 

.PHONY: build push

build:
    docker build -t $(REGISTRY)$(IMAGE_NAME):$(TAG) .

push:
    docker push $(REGISTRY)$(IMAGE_NAME):$(TAG)