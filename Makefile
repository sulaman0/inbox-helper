.PHONY: install test run run-offline review eval eval-offline lint clean

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=inbox_helper --cov-report=term-missing

run:
	python -m inbox_helper run data/messages.json

run-offline:
	python -m inbox_helper run data/messages.json --offline

review:
	python -m inbox_helper review

eval:
	python -m inbox_helper eval

eval-offline:
	python -m inbox_helper eval --offline

clean:
	rm -rf out/ __pycache__ inbox_helper/__pycache__ tests/__pycache__ .pytest_cache
