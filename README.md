# Airtable Contractor Applications Pipeline

This repo provides a detailed guide for setting up and using the Airtable Contractor Application pipeline, which integrates Airtable data with Python scripts for automation, compresses multi-table records into a JSON blob, shortlists candidates based on rules, and enriches/evaluates data using an LLM (Gemini). The pipeline is containerized with Docker and includes a Makefile for easy setup.

## Prerequisites
Python 3.11 or higher (for local runs)

Docker (for containerized runs)

Airtable account with an API key

Gemini API key for LLM integration

Basic familiarity with command-line tools and YAML configuration

## Quickstart

1. Copy `.env.example` to `.env` and fill in your keys.
2.  Create your Airtable base and tables matching config.yaml.
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

# Structure

- `src/` - source modules and pipeline scripts
- `config.yaml` - mapping for Airtable tables and LLM config
- `Dockerfile`, `Makefile` - for containerized runs
- `tests/` - basic unit tests
  
 **SRC/**
   >Data Fetching(src/airtable_utils.py)

   This module retrieves records from the Airtable tables (Applicants, Personal details,Work experience,salary preferences, Shortlist) using the Airtable API.

   
   ![Utilsimage](<img width="2049" height="1400" alt="image" src="https://github.com/user-attachments/assets/b691414b-bc04-4cc4-8307-56d9581f18dc" />
)

   **Snippet**
   * How it works:Connects to Airtable using the provided API key and base ID, retrieves all records from the    specified table, and returns them as a list of dictionaries
   * Output:Raw Airtable records (e.g., [{"id": "rec123", "fields": {"Name": "John Doe", ...}}]).
 
 
 >Data Compression (src/compress.py)

  This module merges records from multiple tables into a single JSON blob per applicant, linking Applicants, Evaluations, and Shortlist data by Application ID.

  
 





