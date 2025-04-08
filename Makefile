.PHONY: bundle deps

SHELL := /bin/bash

deps:
	rm -rf package && \
    mkdir -p package && \
    pip install -q -r requirements.txt --target ./package

function.zip: deps SimpleLambda.py collector.yaml rotel.env
	rm -f function.zip && \
    cd package && zip -q -r ../function.zip . && \
    cd .. && zip -q function.zip SimpleLambda.py collector.yaml rotel.env

bundle: function.zip
