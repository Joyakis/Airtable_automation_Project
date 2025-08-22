import os 
from compress import build_compressed_json
from shortlist import evaluate_shortlist
from llm import call_llm_for_application, format_followups
from airtable_utils import update_record, find_by_field
import json

def run_for_applicant(applicant_id):
    print('Building compressed JSON...')
    payload = build_compressed_json(applicant_id)

    # write compressed JSON back to Applicants record
    rows = find_by_field('applicants', 'Applicant ID', applicant_id)
    if rows:
        rec = rows[0]
        update_record('applicants', rec['id'], {'Compressed JSON':json.dumps(payload)})

    # evaluate shortlist
    ok, reason = evaluate_shortlist(payload)
    print('Shortlist:', ok, reason)

    # call LLM if compressed JSON present
    try:
        payload_json_string = json.dumps(payload)
        llm_text = call_llm_for_application(payload_json_string)

        # parse minimal fields and write back
        summary = ''
        score = None
        followups_raw = []
        collecting_followups = False

        for ln in llm_text.splitlines():
            if ln.startswith('Summary:'):
                summary = ln.split('Summary:')[1].strip()
            elif ln.startswith('Score:'):
                try:
                    score = int(ln.split('Score:')[1].strip())
                except:
                    score = None
            elif ln.startswith('Follow-Ups:'):
                collecting_followups = True
            elif collecting_followups:
                # stop collecting if blank line or another section starts
                if not ln.strip() or ln.endswith(':'):
                    break
                followups_raw.append(ln)

        # format follow-ups using helper from llm.py
        followups = format_followups("\n".join(followups_raw))

        if rows:
            update_record('applicants', rows[0]['id'], {
                'LLM Summary': summary,
                'LLM Score': score or 0,
                'LLM Follow Ups': followups
            })
        print('LLM text saved.')

    except Exception as e:
        print('LLM call failed:', e)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Provide Applicant ID as arg')
    else:
        run_for_applicant(sys.argv[1])
