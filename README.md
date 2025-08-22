# Airtable Contractor Applications Pipeline

This repo provides a starter pipeline to integrate Airtable contractor application data,
compress multi-table records into a single JSON blob, shortlist candidates by rules,
and enrich/evaluate using an LLM (OpenAI). It includes Docker and Makefile for easy setup.

## Quickstart

1. Copy `.env.example` to `.env` and fill in your keys.
2. (Optional) Create your Airtable base and tables matching config.yaml.
3. Build and run with Docker:
   ```bash
   make build
   make run
   ```
4. Or run locally:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python src/run_pipeline.py
   ```

## Structure

- `src/` - source modules and pipeline scripts
- `config.yaml` - mapping for Airtable tables and LLM config
- `Dockerfile`, `Makefile` - for containerized runs
- `tests/` - basic unit tests
