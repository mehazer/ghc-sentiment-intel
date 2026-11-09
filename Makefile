.PHONY: install test lint run web seed up down

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check src tests

run:
	uvicorn ghc.main:app --reload --app-dir src --port 8000

web:
	cd web && npm run dev

seed:
	python scripts/seed_demo.py

up:
	docker compose up --build -d

down:
	docker compose down
