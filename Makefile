SHELL := /bin/bash

PYTHON ?= python3
VENV ?= .venv
ENV_FILE ?= env.local.json
API_URL ?= http://127.0.0.1:3000

DB_CONTAINER ?= postgresql
DB_IMAGE ?= postgres:15
DB_PORT ?= 5432
DB_USER ?= postgres
DB_PASSWORD ?= example
DB_NAME ?= records

.PHONY: install
install:
	@if [ ! -d "$(VENV)" ]; then $(PYTHON) -m venv $(VENV); fi
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r py-lambda/requirements.txt

.PHONY: clean
clean:
	rm -rf $(VENV)
	rm -rf .aws-sam

.PHONY: build
build:
	sam build --use-container

.PHONY: run-local
run-local:
	sam local start-api --env-vars $(ENV_FILE)

.PHONY: pg-start
pg-up:
	@if docker ps -a --format '{{.Names}}' | grep -q '^$(DB_CONTAINER)$$'; then \
		docker start $(DB_CONTAINER); \
	else \
		docker run -d --name $(DB_CONTAINER) -p $(DB_PORT):5432 -e POSTGRES_PASSWORD=$(DB_PASSWORD) -e POSTGRES_DB=$(DB_NAME) $(DB_IMAGE); \
	fi

.PHONY: pg-init
pg-init:
	PGPASSWORD=$(DB_PASSWORD) psql -h localhost -p $(DB_PORT) -U $(DB_USER) -d $(DB_NAME) -f db/init.sql

.PHONY: pg-down
pg-down:
	- docker stop $(DB_CONTAINER)

.PHONY: pg-reset
pg-reset:
	- docker rm -f $(DB_CONTAINER)

.PHONY: psql
psql:
	PGPASSWORD=$(DB_PASSWORD) psql -h localhost -p $(DB_PORT) -U $(DB_USER) -d $(DB_NAME)

.PHONY: curl-post-agent
curl-post-agent:
	curl -X POST \
	${API_URL}/agent \
	-H "Content-Type: application/json" \
	-d '{}'

.PHONY: curl-post-alerts
curl-post-alerts:
	curl -X POST \
	${API_URL}/alerts \
	-H "Content-Type: application/json" \
	-d '{"limit": 2}'

.PHONY: test-agent
test-agent:
	POSTGRES_HOST=localhost \
	POSTGRES_DATABASE=$(DB_NAME) \
	POSTGRES_USER=$(DB_USER) \
	POSTGRES_PASSWORD=$(DB_PASSWORD) \
	python py-lambda/agent.py

.PHONY: test-alerts
test-alerts:
	POSTGRES_HOST=localhost \
	POSTGRES_DATABASE=$(DB_NAME) \
	POSTGRES_USER=$(DB_USER) \
	POSTGRES_PASSWORD=$(DB_PASSWORD) \
	python py-lambda/alerts.py
