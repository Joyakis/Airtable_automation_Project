import os
import sys
import logging
import json
import hashlib
from time import sleep
from dotenv import load_dotenv
from yaml import safe_load
from pyairtable import Api
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

# Load configuration from config.yaml
def _load_config():
    try:
        with open("config.yaml") as f:
            raw = f.read()
        for k, v in os.environ.items():
            raw = raw.replace("${" + k + "}", v)
        config = safe_load(raw)
        logger.info(f"Loaded config: {config}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config.yaml: {str(e)}")
        raise

CONFIG = _load_config()
gemini_api_key = CONFIG["gemini"]["api_key"]
airtable_api_key = CONFIG["airtable"]["api_key"]
airtable_base_id = CONFIG["airtable"]["base_id"]
airtable_applicants_table = CONFIG["airtable"]["tables"]["applicants"]
MODEL = CONFIG["gemini"].get("model", "gemini-1.5-flash")  # Default model
REQUEST_DELAY = 10.0

# Verify API keys
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in configuration")
if not airtable_api_key:
    raise ValueError("AIRTABLE_API_KEY not found in configuration")

logger.info(f"Using Gemini model: {MODEL}, API key: {gemini_api_key[:5]}...")

# Initialize Gemini client
genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel(MODEL)

# Initialize Airtable client
airtable_api = Api(airtable_api_key)
applicants_table = airtable_api.table(airtable_base_id, airtable_applicants_table)

PROMPT = """You are a recruiting analyst. Given this JSON applicant profile, do four things:
1. Provide a concise 75-word summary.
2. Rate overall candidate quality from 1-10 (higher is better).
3. List any data gaps or inconsistencies you notice.
4. Suggest up to three follow-up questions to clarify gaps.

Return exactly:
Summary: <text>
Score: <integer>
Issues: <comma-separated list or 'None'>
Follow-Ups: <bullet list>
"""

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=10, max=120),
    retry=retry_if_exception_type(Exception)
)
def call_llm_for_application(payload_json: str, max_tokens: int = 400):
    logger.info(f"Calling Gemini with payload: {payload_json[:100]}...")
    try:
        response = gemini_model.generate_content(
            PROMPT + "\nApplicant JSON:\n" + payload_json,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": 0.0
            }
        )
        text = response.text
        logger.info(f"Gemini response: {text[:100]}...")
        return text
    except Exception as e:
        logger.exception(f"Gemini call failed: {str(e)}")
    raise


def format_followups(followups_text: str) -> str:
    # Split into lines, clean up, wrap in quotes, and join with bullets
    items = [
        f'•"{line.strip("*•- ").strip()}"'
        for line in followups_text.splitlines()
        if line.strip()
    ]
    return " ".join(items)

def update_airtable(applicant_id: str, result: dict):
    try:
        logger.info(f"Updating Airtable for applicant {applicant_id}")

        followups_formatted = format_followups(result.get("follow_ups", ""))
        
        fields = {
            "LLM Summary": result.get("summary", ""),
            "LLM Score": result.get("score", ""),
            "LLM Follow Ups": followups_formatted
        }

        # 🔎 Debug logs
        logger.info(f"Airtable update payload for {applicant_id}:")
        for k, v in fields.items():
            logger.info(f"  {k} ({type(v)}): {repr(v)}")

        # Send to Airtable
        applicants_table.update(applicant_id, fields)

        logger.info(f"✅ Successfully updated Airtable for applicant {applicant_id}")

    except Exception as e:
        logger.error(f"❌ Failed to update Airtable for {applicant_id}: {str(e)}")
        raise



def evaluate_applicant(applicant_id: str, payload_json: str) -> dict:
    try:
        logger.info(f"Evaluating applicant {applicant_id}")
        json_hash = hashlib.sha256(payload_json.encode()).hexdigest()
        cache_file = f"cache_{applicant_id}.json"
        cached_result = None
        try:
            with open(cache_file, "r") as f:
                cached = json.load(f)
                if cached["hash"] == json_hash:
                    logger.info(f"Using cached result for {applicant_id}")
                    cached_result = cached["result"]
        except FileNotFoundError:
            pass

        if cached_result:
            return cached_result

        llm_response = call_llm_for_application(payload_json)
        result = {
            "summary": "",
            "score": 0,
            "issues": "",
            "follow_ups": "",
            "success": False,
        }
        try:
            if "Summary:" in llm_response:
                parts = llm_response.split("Summary:")[1].split("Score:")
                result["summary"] = parts[0].strip()
                result["success"] = True
            if "Score:" in llm_response:
                score_part = llm_response.split("Score:")[1].split("Issues:")[0].strip()
                result["score"] = int(score_part) if score_part.isdigit() else 0
            if "Issues:" in llm_response:
                issues_part = llm_response.split("Issues:")[1]
                if "Follow-Ups:" in issues_part:
                    result["issues"] = issues_part.split("Follow-Ups:")[0].strip()
            if "Follow-Ups:" in llm_response:
                result["follow_ups"] = llm_response.split("Follow-Ups:")[1].strip()

            with open(cache_file, "w") as f:
                json.dump({"hash": json_hash, "result": result}, f)
        except Exception as parse_error:
            logger.error(f"Failed to parse response for {applicant_id}: {parse_error}")
            result["error"] = f"Parse error: {parse_error}"
            result["success"] = False
        return result
    except Exception as e:
        logger.error(f"Evaluation failed for {applicant_id}: {str(e)}")
        return {"success": False, "error": str(e)}

def main():
    logger.info("Starting script")
    if len(sys.argv) < 2:
        logger.error("No applicant ID provided. Usage: python l2_gemini.py <applicant_id>")
        print("Error: Please provide an applicant ID as a command-line argument.")
        sys.exit(1)

    applicant_ids = [sys.argv[1]]
    for applicant_id in applicant_ids:
        try:
            logger.info(f"Processing applicant {applicant_id}")
            try:
                from compress import build_compressed_json
                payload_json = json.dumps(build_compressed_json(applicant_id))
            except ImportError:
                logger.warning("compress module not found, using dummy JSON")
                payload_json = '{"name": "John Doe", "experience": "5 years at Google"}'

            logger.debug(f"Compressed JSON: {payload_json[:200]}...")
            result = evaluate_applicant(applicant_id, payload_json)
            if result["success"]:
                print("\n=== Evaluation Results ===")
                print(f"LLM Summary: {result['summary']}")
                print(f"LLM Score: {result['score']}")
                print(f"Issues: {result['issues']}")
                print("LLM Followups:")
                print(result["follow_ups"])
                update_airtable(applicant_id, result)
            else:
                print(f"\n❌ Evaluation failed: {result.get('error', 'Unknown error')}")
            sleep(REQUEST_DELAY)
        except Exception as e:
            logger.error(f"Failed to process applicant {applicant_id}: {str(e)}")
            print(f"\n🔥 Error: {str(e)}")

if __name__ == "__main__":
    main()
