# Makefile to run FastAPI app and tests simultaneously
export PYTHONPATH := .
export PYTHONWARNINGS := ignore
run:
	python -m pytest tests/ && python -m uvicorn src.main:app --reload
