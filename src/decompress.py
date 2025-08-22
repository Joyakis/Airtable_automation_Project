import json
import sys
from airtable_utils import find_by_field, create_record, fetch_all_records, update_record, get_table
from datetime import datetime, timezone

def decompress_and_upsert(applicant_id: str):
    """
    Reads the compressed JSON from the Applicants table and updates/upserts
    records in the child tables to reflect the JSON state.
    """
    applicants_table = get_table('applicants')
    
    try:
        # Step 1: Read the compressed JSON from the Applicants table using the ID
        applicant_record = applicants_table.get(applicant_id)
        compressed_json_str = applicant_record['fields'].get('Compressed JSON')
        
        if not compressed_json_str:
            print(f"No compressed JSON found for applicant {applicant_id}. Exiting.")
            return

        compressed_data = json.loads(compressed_json_str)
        
        # Step 2: Update/Upsert Personal Details
        personal_data = compressed_data.get('personal', {})
        # Use the correct table key from your config.yaml
        existing_personal_records = fetch_all_records('personal', f"{{Applicant ID}}='{applicant_id}'")
        
        fields = {
            'Full Name': personal_data.get('Full Name'),
            'Email': personal_data.get('Email'),
            'Location': personal_data.get('Location'),
            'LinkedIn': personal_data.get('LinkedIn')
        }

        if existing_personal_records:
            update_record('personal', existing_personal_records[0]['id'], fields)
            print(f"Updated Personal Details record for applicant {applicant_id}")
        else:
            fields['Applicant ID'] = [applicant_id]
            create_record('personal', fields)
            print(f"Created new Personal Details record for applicant {applicant_id}")
            
        # Step 3: Update/Upsert Work Experience
        # Use the correct table key
        existing_experience_records = fetch_all_records('work', f"{{Applicant ID}}='{applicant_id}'")
        work_table = get_table('work')
        if existing_experience_records:
             for rec in existing_experience_records:
                 work_table.delete(rec['id'])
        
        for exp_fields in compressed_data.get('work', []):
            create_record('work', {
                **exp_fields, # Unpack dictionary
                'Applicant ID': [applicant_id]
            })
        print(f"Recreated Work Experience records for applicant {applicant_id}")
            
        # Step 4: Update/Upsert Salary Preferences
        # Use the correct table key
        salary_data = compressed_data.get('salary', {})
        existing_salary_records = fetch_all_records('salary', f"{{Applicant ID}}='{applicant_id}'")

        fields = {
            'Preferred Rate': salary_data.get('Preferred Rate'),
            'Minimum Rate': salary_data.get('Minimum Rate'),
            'Currency': salary_data.get('Currency'),
            'Availability': salary_data.get('Availability')
        }

        if existing_salary_records:
            update_record('salary', existing_salary_records[0]['id'], fields)
            print(f"Updated Salary Preferences record for applicant {applicant_id}")
        else:
            fields['Applicant ID'] = [applicant_id]
            create_record('salary', fields)
            print(f"Created new Salary Preferences record for applicant {applicant_id}")

        print("Data decompressed successfully.")

    except Exception as e:
        print(f"Error during decompression: {e}")

if __name__ == '__main__':
    try:
        aid = sys.argv[1]
        decompress_and_upsert(aid)
    except IndexError:
        print("Error: You must provide an Applicant ID as a command-line argument.")
        print("Example: python decompress.py recYOURID")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
