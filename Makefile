.DEFAULT_GOAL := help
PY ?= python3
export PATH := $(HOME)/.local/bin:$(PATH)

.PHONY: help install lint format test ingest eval dev demo-offline docker-up docker-down docker-ingest

help:
	@echo "make install | lint | test | demo-offline | ingest | eval | dev | docker-up | docker-ingest | docker-down"

install:
	$(PY) -m pip install -e ".[dev]"

lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

format:
	$(PY) -m ruff format .
	$(PY) -m ruff check --fix .

test:
	APP_ENV=test $(PY) -m pytest -q

demo-offline:
	APP_ENV=test OFFLINE_DEMO=true $(PY) -m scripts.demo_offline

dev:
	set -a && . ./.env && set +a && $(PY) -m uvicorn app.main:app --reload --port 8000

ingest:
	set -a && . ./.env && set +a && $(PY) -m scripts.ingest

eval:
	set -a && . ./.env && set +a && $(PY) -m evals.main

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-ingest:
	docker compose run --rm api python -m scripts.ingest
