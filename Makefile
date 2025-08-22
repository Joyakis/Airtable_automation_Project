.PHONY: build run test

build:
	docker build -t airtable-pipeline .

run:
	docker run --env-file .env airtable-pipeline python src/run_pipeline.py $(APPLICANT_ID)
test:
	docker run --rm airtable-pipeline pytest -q
