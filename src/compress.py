import json
from airtable_utils import fetch_all_records, find_by_field,update_record
from datetime import datetime, timezone

def build_compressed_json(applicant_id):
    # fetch applicant parent row
    apps = find_by_field('applicants', 'Applicant ID', applicant_id)
    if not apps:
        raise ValueError('Applicant not found')
    app_rec = apps[0]
    # fetch child tables by Applicant ID
    personal = find_by_field('personal', 'Applicant ID', applicant_id)
    work = fetch_all_records('work')
    work_filtered = [w['fields'] for w in work if w['fields'].get('Applicant ID') and applicant_id in (w['fields'].get('Applicant ID') or [])]
    salary = find_by_field('salary', 'Applicant ID', applicant_id)
    payload = {
        "version":"1.0.0",
        "applicant_id": applicant_id,
        "personal": personal[0]['fields'] if personal else {},
        "experience": work_filtered,
        "salary": salary[0]['fields'] if salary else {},
        "meta": {
            "compressed_at": datetime.now(timezone.utc).isoformat(),
            "compressor_version": "v1"
        }
    }
    # Update the parent record with the compressed JSON
    update_record('applicants', applicant_id, {'Compressed JSON': json.dumps(payload, indent=2, default=str)})
    
    return payload
    #return json.dumps(payload, indent=2, default=str)

if __name__ == '__main__':
    import sys
    aid = sys.argv[1]
    print(build_compressed_json(aid))
