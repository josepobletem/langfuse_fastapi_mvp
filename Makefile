.PHONY: install install-win run run-win fmt lint test docker-build

install:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

run:
	uvicorn src.app:app --host 0.0.0.0 --port $${PORT:-8000} --reload

install-win:
	@if not exist .venv ( py -3 -m venv .venv )
	.\.venv\Scripts\activate.bat && pip install -r requirements.txt

run-win:
	.\.venv\Scripts\activate.bat && uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload

fmt:
	python -m pip install black isort && black . && isort .

lint:
	python -m pip install flake8 && flake8 src tests

test:
	python -m pip install pytest && pytest -q

docker-build:
	docker build -t langfuse-fastapi-demo:latest .
.PHONY: install install-win run run-win fmt lint test docker-build

install:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

run:
	uvicorn src.app:app --host 0.0.0.0 --port $${PORT:-8000} --reload

install-win:
	@if not exist .venv ( py -3 -m venv .venv )
	.\.venv\Scripts\activate.bat && pip install -r requirements.txt

run-win:
	.\.venv\Scripts\activate.bat && uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload

fmt:
	python -m pip install black isort && black . && isort .

lint:
	python -m pip install flake8 && flake8 src tests

test:
	python -m pip install pytest && pytest -q

docker-build:
	docker build -t langfuse-fastapi-demo:latest .
