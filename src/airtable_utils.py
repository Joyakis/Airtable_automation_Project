import os
import yaml
from pyairtable import Table
from dotenv import load_dotenv
load_dotenv()
import logging
logging.basicConfig(level=logging.INFO)

# Load config.yaml and support environment interpolation
def _load_config():
    with open('config.yaml') as f:
        raw = f.read()
    # naive env substitution for ${VAR}
    for k,v in os.environ.items():
        raw = raw.replace('${' + k + '}', v)
    return yaml.safe_load(raw)

CONFIG = _load_config()

def get_table(table_key: str):
    api_key = CONFIG['airtable']['api_key']
    base_id = CONFIG['airtable']['base_id']
    table_name = CONFIG['airtable']['tables'][table_key]
    return Table(api_key, base_id, table_name)

def fetch_all_records(table_key: str,formula: str = None):
    tbl = get_table(table_key)
    return tbl.all(formula=formula)

def create_record(table_key: str, fields: dict):
    tbl = get_table(table_key)
    return tbl.create(fields)

def update_record(table_key: str, record_id: str, fields: dict):
    tbl = get_table(table_key)
    return tbl.update(record_id, fields)

def find_by_field(table_key: str, field_name: str, value: str):
    tbl = get_table(table_key)
    formula = f"{{{field_name}}}='{value}'"
    return tbl.all(formula=formula)
