# Airtable Contractor Application Pipeline

This project automates the contractor application process by integrating Airtable data with Python scripts. 
It compresses applicant data into JSON blobs, shortlists candidates based on rules, and enriches evaluations using an LLM (Gemini). 
The pipeline is containerized with Docker and includes a Makefile for easy setup.

---

## 🚀 Setup Steps

### Prerequisites
- Python 3.8+ (for local runs)
- Docker (for containerized runs)
- Airtable account with API key
- OpenAI or Gemini API key
- Basic familiarity with CLI tools and YAML

### 1. Clone the Repository
```bash
git clone git@github.com:Joyakis/Airtable_automation_Project.git
cd Airtable_automation_Project
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and update your credentials:

```bash
cp .env.example .env
```

Example `.env`:
```env
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_airtable_base_id
OPENAI_API_KEY=your_openai_api_key
MODEL=gemini-1.5-flash
```

### 3. Airtable Schema
Create a base named **Contractor Application** with tables:

- **Applicants**
  - Applicant ID (Formula)
  - Personal Details (Long Text)
  - Compressed JSON (Long text)
  - LLM Score (Number)
  - LLM Summary (Long text)
  - Shortlist Status (Checkbox)

- **Personal Details**
  - Full Name (Single line text)
  - Email (Email)
  - Location (Single line text)
  - LinkedIn (URL)

- **Shortlistlisted Leads**
  - Applicant (Foreign Key)
  - ScoreReason (Long Text)
  - Shortlist ID (Formula)
  - Compressed JSON(Long Text)

- **Work Experience**
  - Company (Single line text)
  - Title(Single line text)
  - Start(Date)
  - End(Date)
  - Technologies (Single line text)
  - Applicant ID(Foreign Key)

- **Salary Preferences**
- Preferred Rate(Number)
- Minimum Rate(Number)
- Availability(Single line text)
- Currency(Single select)
- Applicant ID(Foreign Key)
    


### 4. Install Dependencies

For local runs:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

For Make runs:
```bash
make build
```
```bash
make run
```

### 5. Run the Pipeline

Local run:
```bash
python src/run_pipeline.py
```

Docker run:
```bash
docker build -t airtable-pipeline .

```
```bash
docker run --env-file .env airtable-pipeline
```


---

## ⚙️ How It Works

### 1. Data Fetching (`src/airtable_utils.py`)
Connects to Airtable and retrieves records.

```python
from pyairtable import Table

def fetch_records(table_name):
    table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, table_name)
    return table.all()
```

### 2. Data Compression (`src/compress.py`)
Merges related records into a single JSON blob.

```python
def build_compressed_json(applicants, details, shortlist):
    return [
        {"application": app, "details": details_map.get(app["id"], []), "shortlist": shortlist_map.get(app["id"], [])}
        for app in applicants
    ]
```

### 3. Data Decompression (`src/decompress.py`)
Splits JSON back into Airtable tables.

```bash
python src/decompress.py <applicant_id>
```

### 4. Shortlisting (`src/shortlist.py`)
Evaluates applicants based on rules.

```python
criteria = {
    "min_experience": 5,
    "required_skills": ["Python", "SQL"]
}
```

Run:
```bash
python src/shortlist.py <applicant_id>
```

### 5. LLM Evaluation (`src/llm.py`)
Uses OpenAI/Gemini to score applicants.

```bash
python src/llm.py <applicant_id>
```

---

## 🔒 Security
- API keys stored in `.env`
- `.gitignore` prevents key leaks
- Docker ensures isolation
- Only necessary applicant fields are shared with LLM

---

## 🛠️ Customization
Extend `src/shortlist.py` to add new rules. Example:

```python
criteria = {
    "min_experience": 5,
    "required_skills": ["Python", "SQL"],
    "min_score": 80
}
```

Move rules into `config.yaml` for dynamic updates.

---

## ✅ Testing

Run unit tests:
```bash
python -m unittest discover tests
```

---

## 📌 Conclusion
This pipeline automates contractor applications with Airtable + Python, 
enhanced by LLM evaluation. Secure, modular, and customizable.

📂 Repository: [Airtable Automation Project](https://github.com/Joyakis/Airtable_automation_Project)
