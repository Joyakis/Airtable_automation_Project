import json
from datetime import datetime
from airtable_utils import create_record, update_record, find_by_field
import re

TIER1 = {'Google', 'Meta', 'OpenAI', 'Microsoft', 'Amazon', 'Apple'}

def years_experience_from_work(experience_list):
    total = 0
    for w in experience_list:
        s = w.get('Start') or w.get('start')
        e = w.get('End') or w.get('end')
        try:
            if s:
                sy = int(str(s)[:4])
                ey = int(str(e)[:4]) if e else datetime.now().year
                total += max(0, ey - sy)
        except (ValueError, IndexError):
            pass
    return total

def evaluate_shortlist(payload_json):
    payload = payload_json
    if isinstance(payload_json, str):
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            print("Error: Invalid JSON payload provided.")
            return False, "Invalid JSON payload"

    aid = payload.get('applicant_id')
    exp = payload.get('experience', [])
    total_years = years_experience_from_work(exp)
    worked_tier1 = any((w.get('company') or w.get('Company')) in TIER1 for w in exp)
    
    salary = payload.get('salary', {})
    
    pref_str = salary.get('preferred_rate') or salary.get('Preferred Rate')
    avail_str = salary.get('availability_hours_per_week') or salary.get('Availability')
    
    try:
        pref = int(pref_str) if pref_str is not None else 99999
        avail_match = re.search(r'\d+', avail_str)
        avail = int(avail_match.group(0)) if avail_match else 0
    except (ValueError, TypeError):
        pref = 99999
        avail = 0
        
    personal = payload.get('personal', {})
    location = personal.get('location') or personal.get('Location', '')
    location_ok = any(x in location for x in [
        'United States', 'Canada', 'United Kingdom', 'Germany', 'India'
    ])
    
    exp_ok = (total_years >= 4) or worked_tier1
    comp_ok = (pref <= 100) and (avail >= 20)
    all_ok = exp_ok and comp_ok and location_ok
    
    reason = f"exp:{total_years}, tier1:{worked_tier1}, pref:{pref}, avail:{avail}, location_ok:{location_ok}"
    
    try:
        rows = find_by_field('applicants', 'Applicant ID', aid)
        if not rows:
            print(f"⚠️ No applicant found with ID {aid}")
            return False, "Applicant not found"
        
        applicant_record_id = rows[0]['id']

        if all_ok:
            # ✅ Passed qualifications
            print("Attempting to create a new record in Shortlisted Leads...")
            existing_shortlist = find_by_field('shortlisted', 'Applicant', aid)
            if not existing_shortlist:
                create_record('shortlisted', {
                    'Applicant': [applicant_record_id],
                    'Compressed JSON': json.dumps(payload_json, default=str),
                    'Score Reason': reason
                })
                print("Successfully created a new record in Shortlisted Leads.")

            print("Updating Applicants table → Shortlist status = True...")
            update_record('applicants', applicant_record_id, {'Shortlist status': True})
            print("✅ Applicant marked as shortlisted.")

        else:
            # ❌ Did not pass qualifications
            print("Applicant did not meet qualifications. Updating Applicants table → Shortlist status = False...")
            update_record('applicants', applicant_record_id, {'Shortlist status': False})
            print("❌ Applicant marked as not shortlisted.")

    except Exception as e:
        print(f"An error occurred during Airtable API calls: {e}")
            
    return all_ok, reason

def find_applicant_record_id(applicant_id):
    rows = find_by_field('applicants', 'Applicant ID', applicant_id)
    return rows[0]['id'] if rows else None

if __name__ == '__main__':
    import sys
    try:
        aid = sys.argv[1]
        from compress import build_compressed_json
        payload_from_db = build_compressed_json(aid)
        ok, reason = evaluate_shortlist(payload_from_db)
        print('Shortlist result:', ok, reason)
    except IndexError:
        print("Error: You must provide an Applicant ID as a command-line argument.")
        print("Example: python shortlist.py recYOURID")
    except ValueError as e:
        print(f"Error: {e}")
